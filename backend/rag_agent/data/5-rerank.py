"""
重新排序：从 RRF 中获取前 50 个候选项，并使用交叉编码器重新排序。返回前 10 个。

双编码器（来自 3-embed.py 的密集检索器）分别对查询和文档进行嵌入，然后通过余弦相似度进行比较。交叉编码器将查询和文档输入同一个模型，并返回单个相关性分数。交叉编码器较慢，但联合注意力能够捕捉两个独立嵌入所遗漏的细微差别。

We use Cohere rerank-v4.0-fast.

More info: https://docs.cohere.com/docs/rerank-overview
"""

import os
import cohere
from dotenv import load_dotenv

load_dotenv()
co = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))
RERANK_MODEL = "rerank-v4.0-fast"


# --------------------------------------------------------------
# Step 1: Load retrievers and corpus
# --------------------------------------------------------------
from pathlib import Path
import bm25s
import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "BAAI/bge-base-en-v1.5"
)

ROOT = Path(__file__).parent.parent
DATA_DIR = Path(__file__).parent / "fiqa"
BM25_DIR = ROOT / "indexes" / "bm25"
DENSE_DIR = ROOT / "indexes" / "dense"


def load_corpus() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "corpus.parquet")


# --------------------------------------------------------------
# BM25
# --------------------------------------------------------------


class BM25Retriever:
    def __init__(self) -> None:
        self._retriever = bm25s.BM25.load(str(BM25_DIR))
        self._doc_ids = (BM25_DIR / "doc_ids.txt").read_text().splitlines()

    def search(self, query: str, k: int = 10) -> list[tuple[str, float]]:
        tokens = bm25s.tokenize([query], stopwords="en")
        indices, scores = self._retriever.retrieve(tokens, k=k)
        return [(self._doc_ids[i], float(scores[0][j])) for j, i in enumerate(indices[0].tolist())]


# --------------------------------------------------------------
# Dense
# --------------------------------------------------------------


class DenseRetriever:
    def __init__(self) -> None:
        corpus = load_corpus()
        self._doc_ids = corpus["_id"].tolist()
        raw = np.load(DENSE_DIR / "embeddings.npy")
        self._embeddings = raw / np.linalg.norm(raw, axis=1, keepdims=True)

    def _embed_query(self, query: str) -> np.ndarray:
        response = model.encode(query, normalize_embeddings=True)
        return np.array(response, dtype=np.float32)

    def search(self, query: str, k: int = 10) -> list[tuple[str, float]]:
        scores = self._embeddings @ self._embed_query(query)
        top_k = np.argsort(-scores)[:k]
        return [(self._doc_ids[i], float(scores[i])) for i in top_k]
    

bm25 = BM25Retriever()
dense = DenseRetriever()
corpus_by_id = load_corpus().set_index("_id")


# --------------------------------------------------------------
# Step 2: Rerank with a cross-encoder
# --------------------------------------------------------------
from collections import defaultdict
# rrf
def reciprocal_rank_fusion(
    rankings: list[list[str]], k: int = 60
) -> list[tuple[str, float]]:
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: -x[1])


def hybrid_candidates(
    query: str,
    bm25: BM25Retriever,
    dense: DenseRetriever,
    candidate_k: int = 50,
) -> list[tuple[str, float]]:
    bm25_ids = [doc_id for doc_id, _ in bm25.search(query, k=candidate_k)]
    dense_ids = [doc_id for doc_id, _ in dense.search(query, k=candidate_k)]
    return reciprocal_rank_fusion([bm25_ids, dense_ids])[:candidate_k]


def search_reranked(
    query: str, k: int = 10, candidate_k: int = 50
) -> list[tuple[str, float]]:
    candidates = hybrid_candidates(query, bm25, dense, candidate_k=candidate_k)
    candidate_ids = [doc_id for doc_id, _ in candidates]
    candidate_texts = [corpus_by_id.loc[d, "text"] for d in candidate_ids]

    response = co.rerank(
        model=RERANK_MODEL,
        query=query,
        documents=candidate_texts,
        top_n=k,
    )

    return [(candidate_ids[r.index], r.relevance_score) for r in response.results]


# --------------------------------------------------------------
# Step 3: Compare hybrid vs hybrid + rerank
# --------------------------------------------------------------


def show(label: str, results: list[tuple[str, float]]) -> None:
    print(f"\n{label}")
    for i, (doc_id, score) in enumerate(results[:5], 1):
        text = corpus_by_id.loc[doc_id, "text"]
        print(f"  {i}. [{score:.4f}] {doc_id}  {text[:70]}")


if __name__ == "__main__":
    query = "Where should I park my rainy-day fund?"
    print(f"Query: {query}")

    show("Hybrid (RRF) only", hybrid_candidates(query, bm25, dense, candidate_k=50)[:5])
    show("Hybrid + Cohere rerank-v4.0-fast", search_reranked(query, k=5))