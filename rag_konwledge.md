# RAG 检索增强生成技术文档

## 1. 什么是 RAG

RAG（Retrieval-Augmented Generation，检索增强生成）是一种结合信息检索与大语言模型生成的技术范式。它先从外部知识库中检索与用户问题相关的文档片段，再将这些片段作为上下文提供给大语言模型，从而生成更准确、更 grounded 的回答。

RAG 的核心价值在于：

- 解决大模型知识截止和幻觉问题
- 支持私有知识、实时知识的接入
- 提高回答的可追溯性和可控性

## 2. RAG 典型流水线

标准 RAG 流水线通常包含以下步骤：

1. 文档解析与切分（Chunking）
2. 向量化（Embedding）并建立索引
3. 用户查询到来时进行检索（Retrieval）
4. （可选）重排序（Rerank）
5. 将检索到的上下文与问题一起送给 LLM 生成答案
6. （可选）对生成结果进行评估（Evaluation）

## 3. 检索方式对比

### 3.1 Dense Retrieval（稠密检索）

使用向量嵌入模型将查询和文档映射到同一语义空间，通过余弦相似度或内积计算相关性。优点是能捕捉语义相似性，对同义词、改写鲁棒；缺点是对关键词精确匹配能力较弱，且需要高质量的 embedding 模型。

### 3.2 Sparse Retrieval（稀疏检索，以 BM25 为代表）

BM25 是经典的基于词频的排序算法，利用 TF-IDF 思想计算文档与查询的相关性。优点是对关键词匹配精确、可解释性强、无需训练；缺点是难以处理语义相近但用词不同的情况。

### 3.3 混合检索（Hybrid Retrieval）

同时使用 Dense 和 Sparse 两种检索方式，再通过融合算法合并结果。实践中被证明能显著提升召回率和最终回答质量。

## 4. 结果融合算法：RRF

RRF（Reciprocal Rank Fusion）是一种简单而有效的多路检索结果融合方法。其核心公式为：

score(d) = Σ 1 / (k + rank_i(d))

其中 rank_i(d) 是文档 d 在第 i 路检索结果中的排名，k 通常取 60。RRF 不依赖原始分数的尺度，只使用排名信息，因此对异构检索器非常友好。

## 5. 重排序（Rerank）

在召回阶段获得候选文档后，使用更强的交叉编码器（Cross-Encoder）模型对「查询-文档」对进行精细打分，并重新排序。常见模型包括 Cohere Rerank、bge-reranker、Jina Reranker 等。Rerank 能显著提升 Top-K 结果的精度，是当前生产级 RAG 的标配。

## 6. 评测指标

使用 LangSmith 等平台可构建自动化评测体系，常用指标包括：

- **Correctness（正确性）**：生成答案是否与参考答案语义一致、事实正确。
- **Groundedness（忠实性/ groundedness）**：答案是否严格基于检索到的上下文，没有凭空捏造。
- **Retrieval Relevance（检索相关性）**：检索到的文档是否真正与问题相关。
- **Context Precision / Recall**：上下文的精确率和召回率。

通过对比不同检索策略（仅 Dense vs BM25+Dense+RRF+Rerank）的指标变化，可以量化优化效果。

## 7. 实践建议

- 召回阶段 candidate_k 建议设为最终 k 的 3~5 倍。
- 混合检索 + RRF 通常比单一检索提升明显。
- 加入 Rerank 后 Top-5 精度提升最为显著。
- 建议构建 20~50 条高质量测试集，覆盖事实型、对比型、多跳推理等问题。
- 使用 LangSmith 记录每次实验的 traces 和评估结果，便于对比和面试展示。

## 8. 常见问题

Q: 为什么混合检索比单一 Dense 更好？
A: Dense 擅长语义，BM25 擅长关键词。两者互补，RRF 能有效融合双方优势。

Q: Rerank 一定要用吗？
A: 在对精度要求高的场景强烈推荐。如果延迟敏感且候选质量已经很高，可以关闭。

Q: 如何判断检索链路是否有效？
A: 通过 correctness、groundedness、retrieval relevance 等指标进行量化对比，而不是仅凭主观感受。
