from collections import defaultdict
from sqlalchemy import text
from backend.rag_agent.models import ConversationDocument, Document, get_embedding_model
import bm25s
import os
import cohere
from dotenv import load_dotenv

load_dotenv()

co = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))


class HybridRetriever:
    def __init__(
        self,
        db,
        conversation_id: int,
        rerank_model: str = "rerank-multilingual-v3.0",
        cohere_client=co,
    ):
        self.db = db
        self.conversation_id = conversation_id

        # 1. 找到当前会话关联的所有逻辑文档 ID
        user_doc_ids = (
            db.query(ConversationDocument.user_document_id)
            .filter(ConversationDocument.conversation_id == conversation_id)
            .all()
        )
        user_doc_ids = [row[0] for row in user_doc_ids if row[0] is not None]

        if not user_doc_ids:
            print(f"警告: conversation_id={conversation_id} 没有关联任何文档")
            self.doc_ids = []
            self.documents = []
            self.doc_store = {}
            self.bm25 = None
            self.model = get_embedding_model()
            self.co = cohere_client
            self.rerank_model = rerank_model
            return

        # 2. 找到这些逻辑文档下的所有切片
        documents = (
            db.query(Document)
            .filter(Document.user_document_id.in_(user_doc_ids))
            .all()
        )

        self.doc_ids = [d.id for d in documents]
        self.documents = [d.content for d in documents]
        self.doc_store = {d.id: d.content for d in documents}

        print(f"会话 {conversation_id} 加载了 {len(documents)} 个 chunks")

        # BM25
        if self.documents:
            corpus_tokens = bm25s.tokenize(self.documents, stopwords="zh")
            self.bm25 = bm25s.BM25()
            self.bm25.index(corpus_tokens)
        else:
            self.bm25 = None

        self.model = get_embedding_model()
        self.co = cohere_client
        self.rerank_model = rerank_model

    def _bm25_search(self, query: str, k: int):
        if not self.documents or self.bm25 is None:
            return []
        k = min(k, len(self.documents))
        query_tokens = bm25s.tokenize([query], stopwords="zh")
        indices, scores = self.bm25.retrieve(query_tokens, k=k)
        return [
            (self.doc_ids[i], float(scores[0][j]))
            for j, i in enumerate(indices[0].tolist())
        ]

    def _dense_search(self, query: str, k: int):
        if not self.doc_ids:
            return []
        k = min(k, len(self.doc_ids))
        query_emb = self.model.encode(query, normalize_embeddings=True)

        sql = text("""
            SELECT 
                id, 
                1 - (embedding <=> :vector) AS score
            FROM documents
            WHERE id = ANY(:ids)
            ORDER BY embedding <=> :vector
            LIMIT :k
        """)

        results = self.db.execute(
            sql,
            {
                "vector": str(query_emb.tolist()),
                "ids": self.doc_ids,
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

    def _get_documents(self, doc_ids):
        rows = (
            self.db.query(Document)
            .filter(Document.id.in_(doc_ids))
            .all()
        )
        return {row.id: row.content for row in rows}

    def search(
        self,
        query: str,
        k: int = 5,
        candidate_k: int = 20,
        use_rerank: bool = True,
    ):
        corpus_size = len(self.documents)
        if corpus_size == 0:
            return []

        k = min(k, corpus_size)
        candidate_k = min(candidate_k, corpus_size)

        # 1. 双路召回
        bm25_ids = [doc_id for doc_id, _ in self._bm25_search(query, candidate_k)]
        dense_ids = [doc_id for doc_id, _ in self._dense_search(query, candidate_k)]

        # 2. RRF 融合
        fused = self._rrf([bm25_ids, dense_ids])[:candidate_k]
        candidate_ids = [doc_id for doc_id, _ in fused]

        if not use_rerank or self.co is None:
            return [
                {"id": doc_id, "score": score, "content": self.doc_store.get(doc_id, "")}
                for doc_id, score in fused[:k]
            ]

        # 3. Rerank
        doc_map = self._get_documents(candidate_ids)
        candidate_texts = [doc_map[doc_id] for doc_id in candidate_ids if doc_id in doc_map]

        if not candidate_texts:
            return []

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