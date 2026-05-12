from langchain.tools import tool
from rag_agent.retriever import retriever, deduplicate_docs

@tool("retrieve_knowledge")
def retrieve_knowledge(query: str) -> dict:
    """从上传的文档知识库中检索最相关的内容"""
    docs = retriever.invoke(query)
    if not docs:
        return {"answer": "抱歉，知识库中没有相关信息。", "docs": []}

    unique_docs = deduplicate_docs(docs)

    context = "\n\n".join([
        f"[来源: {doc.metadata.get('source', 'unknown')} | 页码: {doc.metadata.get('page', 'unknown')}]\n{doc.page_content}"
        for doc in unique_docs
    ])

    return {
        "answer": f"[知识库检索结果]\n{context}",
        "docs": unique_docs
    }

tools = [retrieve_knowledge]
