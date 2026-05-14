from rag_agent.vectorstore import vectorstore

retriever = vectorstore.as_retriever(
    search_type="mmr", # 使用 MMR 检索方式 (最大边际相关性)兼顾相关性 + 多样性
    search_kwargs={
        "k": 2,       # 最终返回 2 个文档
        "fetch_k": 8,  # 先召回 8 个候选文档(先用相似度找出 8 条，再用 MMR 算法从中挑选出 k=2 条。)
        "lambda_mult": 0.7 ## 多样性权重 越接近 1：越重视相关性（结果更相似）- 越接近 0：越重视多样性（结果差异更大
    }
)

def deduplicate_docs(docs):
    seen = set()
    unique_docs = []
    for d in docs:
        key = (d.metadata.get("source"), d.metadata.get("page"), d.page_content[:400])
        if key not in seen:
            seen.add(key)
            unique_docs.append(d)
    return unique_docs
