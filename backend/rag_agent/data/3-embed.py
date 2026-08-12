"""
密集检索。使用 text-embedding-3-small 将每个文档嵌入一次，
将矩阵缓存为 numpy，然后通过余弦相似度回答查询。

密集嵌入捕捉释义。询问“停放我的应急基金”
匹配一份文件，上面写着“短期储蓄的安全场所”，尽管
没有单词重叠。他们输在精确的符号和罕见的术语上（BM25 获胜）
条件：股票代码、税表代码、法规名称）。

More info: https://platform.openai.com/docs/guides/embeddings
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv(override=True)
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "BAAI/bge-base-en-v1.5"
)

DATA_DIR = Path(__file__).parent / "data" / "fiqa"
INDEX_DIR = Path(__file__).parent / "indexes" / "dense"
INDEX_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------
# Step 1: Embed the corpus in batches
# --------------------------------------------------------------


def embed_batch(texts: list[str]) -> np.ndarray:
    """Embed a batch of texts and return a numpy array."""
    vectors = model.encode(texts)
    return np.array(vectors, dtype=np.float32)


def build_index(doc_texts: list[str], batch_size: int = 256) -> np.ndarray:
    """Embed the full corpus in batches with a progress bar."""
    chunks = []
    for i in tqdm(range(0, len(doc_texts), batch_size), desc="Embedding"):
        chunks.append(embed_batch(doc_texts[i : i + batch_size]))
    return np.vstack(chunks)  # stack batches into one (N, 1024) matrix


# --------------------------------------------------------------
# Step 2: Build or load the cached embedding matrix
# --------------------------------------------------------------

corpus = pd.read_parquet(DATA_DIR / "corpus.parquet")
doc_ids = corpus["_id"].tolist()

# OpenAI rejects empty strings in the embeddings endpoint. ~38 FiQA docs have
# blank text; we swap in a placeholder so the row order stays aligned with
# the BM25 index (which tolerates empty text just fine).
doc_texts = [t.strip() or "[empty document]" for t in corpus["text"].tolist()]

embeddings_path = INDEX_DIR / "embeddings.npy"
if embeddings_path.exists():
    print(f"Loading cached embeddings from {embeddings_path}")
    doc_embeddings = np.load(embeddings_path)
else:
    print(f"Embedding {len(doc_texts)} docs ( at BAAI/bge-base-en-v1.5)")
    doc_embeddings = build_index(doc_texts)
    np.save(embeddings_path, doc_embeddings)

# Pre-normalize once so cosine similarity becomes a single dot product later.
doc_embeddings_normed = doc_embeddings / np.linalg.norm(
    doc_embeddings, axis=1, keepdims=True
)

# --------------------------------------------------------------
# Step 3: Query by cosine similarity
# --------------------------------------------------------------


def search_dense(query: str, k: int = 10) -> list[tuple[str, float]]:
    """Return the top-k (doc_id, similarity) pairs for a query."""
    query_vec = embed_batch([query])[0]
    query_vec /= np.linalg.norm(query_vec)
    scores = doc_embeddings_normed @ query_vec
    top_k = np.argsort(-scores)[:k]
    return [(doc_ids[i], float(scores[i])) for i in top_k]


if __name__ == "__main__":
    query = "Where should I park my rainy-day fund?"
    print(f"\nQuery: {query}\n")
    for i, (doc_id, score) in enumerate(search_dense(query, k=5), 1):
        text = corpus.loc[corpus["_id"] == doc_id, "text"].iloc[0]
        print(f"{i}. [{score:.3f}] {doc_id} {text}\n")