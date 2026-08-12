# RAG 检索链路升级修改指南

这份文件的目标是：把当前项目从“单一 dense embedding 检索”升级为“Query Rewrite → Hybrid Retrieval → RRF → Cross Encoder rerank → LLM”。

## 你要修改的核心文件

- backend/rag_agent/retriever.py
- backend/rag_agent/tools.py
- backend/rag_agent/config.py
- backend/rag_agent/requirements.txt
- backend/rag_agent/llm.py（可选，若要复用更稳妥的 rewrite prompt）

---

## 第一阶段：把检索逻辑从单一向量检索改成多阶段流程

### 1. 先替换 retriever.py 的内容

当前文件里现在还是直接用 Chroma 的 retriever，这会让流程过于单调。

你要做的是把它改成一个“检索服务”，内部流程如下：

1. 先对用户问题做 Query Rewrite
2. 分别调用 BM25 和 Dense 检索
3. 用 RRF 合并候选文档
4. 用 Cross Encoder 做 rerank
5. 返回 top-k 文档给 LLM

建议的结构如下：

```python
from typing import List, Tuple
from rag_agent.llm import llm
from rag_agent.vectorstore import vectorstore


class HybridRetriever:
    def __init__(self):
        self._bm25 = None
        self._dense = None
        self._reranker = None

    def _rewrite_query(self, query: str) -> List[str]:
        # 先用 LLM 生成 2~3 个重写 query
        return [query]

    def _reciprocal_rank_fusion(self, rankings, k=60):
        # 参考 data/4-rrf.py 的实现
        return []

    def _run_bm25(self, query: str, k: int = 20):
        return []

    def _run_dense(self, query: str, k: int = 20):
        return []

    def _rerank(self, query: str, docs, k: int = 5):
        return docs[:k]

    def invoke(self, query: str):
        rewritten_queries = self._rewrite_query(query)
        candidate_lists = []

        for q in rewritten_queries:
            bm25_docs = self._run_bm25(q, k=20)
            dense_docs = self._run_dense(q, k=20)
            fused = self._reciprocal_rank_fusion([bm25_docs, dense_docs])
            candidate_lists.append(fused)

        final_candidates = self._reciprocal_rank_fusion(candidate_lists)
        return self._rerank(query, final_candidates, k=5)
```

### 2. 先不要把所有功能一次性写满

你可以先做一个“最小可运行版本”：

- Query Rewrite 先直接返回原始 query
- BM25 先从现有索引读取
- Dense 先从 embeddings.npy 读取
- RRF 先简单实现
- rerank 先暂时跳过，或者只保留一个占位函数

这样你可以先把流程跑起来，再逐步完善。

---

## 第二阶段：把 tools.py 接到新检索器

当前 tools.py 里调用的是：

```python
from rag_agent.retriever import retriever, deduplicate_docs
```

你需要把它改成：

```python
from rag_agent.retriever import hybrid_retriever, deduplicate_docs
```

然后把原来的逻辑改成：

```python
@tool("retrieve_knowledge")
def retrieve_knowledge(query: str) -> dict:
    docs = hybrid_retriever.invoke(query)
    if not docs:
        return {"context": "", "docs": []}

    unique_docs = deduplicate_docs(docs)
    context = "\n\n".join([doc.page_content for doc in unique_docs])

    return {
        "context": context,
        "docs": unique_docs,
    }
```

这一步的关键是：保持 agent 的接口不变，也就是工具仍然返回 context 和 docs。

---

## 第三阶段：先从现有脚本里“借”逻辑

你已经在 data/ 目录里有这些脚本：

- data/2-bm25.py
- data/3-embed.py
- data/4-rrf.py
- data/5-rerank.py

建议你优先复用它们的思路，而不是重新发明一套。

### 复用点 1：BM25

从 data/2-bm25.py 里拿到：

- bm25s 的 tokenize
- BM25.load 的方式
- doc_ids 的读取逻辑

### 复用点 2：Dense

从 data/3-embed.py 里拿到：

- embeddings.npy 的加载
- 归一化向量
- 余弦相似度计算

### 复用点 3：RRF

从 data/4-rrf.py 里拿到：

```python
def reciprocal_rank_fusion(rankings, k=60):
    scores = defaultdict(float)
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: -x[1])
```

### 复用点 4：Rerank

从 data/5-rerank.py 里拿到：

- 候选文档文本拼接
- cross encoder 的输入结构
- top-k 排序逻辑

---

## 第四阶段：加 Query Rewrite

Query Rewrite 不需要一上来就很复杂。

你可以先用一个很简单的版本：

```python
def _rewrite_query(self, query: str) -> List[str]:
    prompt = f"""
    请把下面的问题改写成 2 个更适合检索的版本：
    {query}
    """

    response = llm.invoke(prompt)
    rewritten = response.content.strip()
    if not rewritten:
        return [query]
    return [query, rewritten]
```

注意：

- 这里先不要追求很高质量
- 只要能让原问题变成更“检索友好”的表达即可
- 如果 LLM 调用失败，回退到原 query

---

## 第五阶段：加配置开关

为了避免因为缺少 reranker 模型而导致整个流程直接挂掉，建议在 config.py 里加几个简单开关：

```python
ENABLE_QUERY_REWRITE = True
ENABLE_RERANK = False
```

然后在 retriever 中根据开关决定是否执行这一步。

---

## 第六阶段：验证

改完后，建议依次执行下面几个验证：

### 1. 先测试检索是否能返回文档

```bash
python -c "from rag_agent.retriever import hybrid_retriever; print(hybrid_retriever.invoke('What is a rainy day fund?')[:2])"
```

### 2. 测试 agent tool 是否还能工作

```bash
python -c "from rag_agent.tools import retrieve_knowledge; print(retrieve_knowledge('What is a rainy day fund?'))"
```

### 3. 检查是否没有报错

如果你看到：

- 文档列表非空
- context 不为空
- agent 工具还能调用

就说明第一版升级已经成功。

---

## 推荐修改顺序

1. 先改 retriever.py
2. 再改 tools.py
3. 再加 config.py 的开关
4. 最后加 reranker 相关依赖

这样最不容易一开始就卡住。

---

## 最小可行目标

你不用一口气把所有功能都做完，先实现这个最小版本即可：

- 原始 query 进来
- 走 BM25 + Dense
- 做 RRF
- 返回 top-3 文档

这已经比当前“只有 dense embedding”强很多了。
