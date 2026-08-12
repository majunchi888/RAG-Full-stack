"""
倒数秩融合（RRF）。将 BM25 和密集检索合二为一
排名名单。

天真的想法是“平均分数”，但 BM25 分数是无界的，
余弦相似度位于 [0, 1] 中。解决办法是融合排名，而不是分数。

    rrf_score(d) = 每个检索器 r 的总和 1 /(k +rank_r(d))

k 是一个平滑常数，通常为 60。2009 年的原始论文称为
它“简单但有效”，这仍然是 2026 年的共识。
More info: https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
"""

from collections import defaultdict
# from utils.retrievers import BM25Retriever, DenseRetriever, load_corpus

K_RRF = 60


# --------------------------------------------------------------
# Step 1: The fusion function
# --------------------------------------------------------------


def reciprocal_rank_fusion(
    rankings: list[list[str]], k: int = K_RRF
) -> list[tuple[str, float]]:
    """将多个 doc_ids 排名列表融合到一个排名列表中。"""
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: -x[1])


# --------------------------------------------------------------
# Step 2: Load both retrievers
# --------------------------------------------------------------
import os
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
corpus = load_corpus()


# --------------------------------------------------------------
# Step 3: Search both, fuse, compare
# --------------------------------------------------------------


def search_hybrid(
    query: str, k: int = 10, candidate_k: int = 50
) -> list[tuple[str, float]]:
    """Retrieve top candidate_k from each retriever, fuse, return top k."""
    bm25_ids = [doc_id for doc_id, _ in bm25.search(query, k=candidate_k)]
    dense_ids = [doc_id for doc_id, _ in dense.search(query, k=candidate_k)]
    return reciprocal_rank_fusion([bm25_ids, dense_ids])[:k]


def show(label: str, results: list[tuple[str, float]]) -> None:
    print(f"\n{label}")
    for i, (doc_id, score) in enumerate(results[:5], 1):
        text = corpus.loc[corpus["_id"] == doc_id, "text"].iloc[0]
        print(f"  {i}. [{score:.4f}] {doc_id}  {text[:70]}")


if __name__ == "__main__":
    query = "Where should I park my rainy-day fund?"
    print(f"Query: {query}")

    show("BM25 only", bm25.search(query, k=5))
    show("Dense only", dense.search(query, k=5))
    show("Hybrid (RRF)", search_hybrid(query, k=5))