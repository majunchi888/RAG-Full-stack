from collections import defaultdict
from backend.rag_agent.database import SessionLocal, get_db
from sqlalchemy import sql, text
from backend.rag_agent.models import ConversationDocument, embedding_model, Document
import numpy as np
import bm25s
import os
import cohere
from dotenv import load_dotenv

load_dotenv()
co = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))
RERANK_MODEL = "rerank-v4.0-fast"


class HybridRetriever:
    def __init__(
        self,
        db,
        conversation_id: str,
        doc_id: list[str] | None = None,
        rerank_model: str = "rerank-multilingual-v3.0",  # 你的 Cohere 模型名
        cohere_client=co,
    ):
        
        self.db = db
        self.conversation_id = conversation_id

        # 1. 找到当前 conversation 对应的文件
        conversation_docs = (
            db.query(ConversationDocument.document_doc_id)
            .filter(
                ConversationDocument.conversation_id == conversation_id
            )
            .all()
        )

        doc_ids = [str(row[0]) for row in conversation_docs if row[0] is not None]
        print(doc_ids)

        # 2. 找到这些文件对应的所有 chunks
        documents = (
            db.query(Document)
            .filter(Document.doc_id.in_(doc_ids))
            .all()
        )
    

        self.doc_ids = [d.id for d in documents]
        self.documents = [d.content for d in documents]
        self.doc_store = {d.id: d.content for d in documents}

        print("实际加载的 chunk 主键 id 列表:", [d.id for d in documents])
        print("实际加载的 doc_id 列表:", [d.doc_id for d in documents])

        # ---------- BM25 ----------
        corpus_tokens = bm25s.tokenize(self.documents, stopwords="zh")
        self.bm25 = bm25s.BM25()
        self.bm25.index(corpus_tokens)

        # ---------- Dense ----------
        self.model = embedding_model
        embeddings = self.model.encode(self.documents, normalize_embeddings=True)
        # self.embeddings = np.array(embeddings, dtype=np.float32)
        

        # ---------- Reranker ----------
        self.co = cohere_client
        self.rerank_model = rerank_model
     

    def _bm25_search(self, query: str, k: int):
        
        k = min(k, len(self.documents))
        query_tokens = bm25s.tokenize([query], stopwords="zh")
        indices, scores = self.bm25.retrieve(query_tokens, k=k)
        return [
            (self.doc_ids[i], float(scores[0][j]))
            for j, i in enumerate(indices[0].tolist())
        ]

    def _dense_search(self, query: str, k: int) :
        k = min(k, len(self.documents))
        query_emb = self.model.encode(query, normalize_embeddings=True)

        sql = text(
            """
            SELECT 
                id, 
                1 - (embedding <=> :vector) AS score
            FROM documents
            WHERE id = ANY(:ids)
            ORDER BY embedding <=> :vector
            LIMIT :k
            """
        )
    
        results = self.db.execute(
            sql,
            {
                "vector": str(query_emb.tolist()),
                "ids": self.doc_ids,   # 只搜索当前会话的文档
                "k": k
            }
        )
    
        return [(row.id, float(row.score)) for row in results]

    @staticmethod
    def _rrf(rankings, k: int = 60):
        scores = defaultdict(float)
        for ranking in rankings:
            for rank, doc_id in enumerate(ranking, start=1):
                scores[doc_id] += 1.0 / (k + rank)
        return sorted(scores.items(), key=lambda x: -x[1])

    def _get_documents(self, doc_id):

        rows = (
            self.db.query(Document)
            .filter(
                Document.id.in_(doc_id)
            )
            .all()
        )

        return {
            row.id: row.content
            for row in rows
        }

    def search(
        self,
        query: str,
        k: int = 5,
        candidate_k: int = 20,
        use_rerank: bool = True,
    ) -> list[tuple[str, float]]:
        """
        混合检索入口
        :param query: 查询语句
        :param k: 最终返回数量
        :param candidate_k: 召回阶段候选数量
        :param use_rerank: 是否使用 Cohere Rerank
        """
        corpus_size = len(self.documents)
        k = min(k, corpus_size)
        candidate_k = min(candidate_k, corpus_size)

        # 1. 双路召回
        bm25_ids = [doc_id for doc_id, _ in self._bm25_search(query, candidate_k)]
        dense_ids = [doc_id for doc_id, _ in self._dense_search(query, candidate_k)]

        # 2. RRF 融合
        fused = self._rrf([bm25_ids, dense_ids])[:candidate_k]
        print(fused[:k])
        candidate_ids = [doc_id for doc_id, _ in fused]
        
        if not use_rerank or self.co is None:
            # 不使用 rerank，直接返回 RRF 结果
            return fused[:k]

        # 3. Rerank
        doc_map = self._get_documents(candidate_ids)
        candidate_texts = [doc_map[doc_id] for doc_id in candidate_ids]

        response = self.co.rerank(
            model=self.rerank_model,
            query=query,
            documents=candidate_texts,
            top_n=k,
        )

        return [
            {
                "id": candidate_ids[r.index],
                "score": float(r.relevance_score),
                "content": candidate_texts[r.index]
            }
            for r in response.results
        ]

