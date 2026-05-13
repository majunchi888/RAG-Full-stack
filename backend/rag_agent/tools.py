from langchain.tools import tool
from rag_agent.retriever import retriever, deduplicate_docs

@tool("retrieve_knowledge")
def retrieve_knowledge(query: str) -> dict:
    """从知识库检索相关文档内容"""

    docs = retriever.invoke(query)
    if not docs:
        return {"context": "", "docs": []}

    unique_docs = deduplicate_docs(docs)

    context = "\n\n".join([
        doc.page_content
        for doc in unique_docs
    ])

    return {
        "context": context,
        "docs": unique_docs
    }

tools = [retrieve_knowledge]
