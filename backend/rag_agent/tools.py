from typing import Annotated

from fastapi import Depends
from langchain.tools import tool
from sqlalchemy.orm import Session
from backend.rag_agent.database import get_db
from backend.rag_agent.models import Document
from backend.rag_agent.retriever import HybridRetriever

@tool("retrieve_knowledge")
def retrieve_knowledge(query: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    """Useful for when you need to answer questions about a document."""

    retriever = HybridRetriever(db=db)

    results = retriever.search(
        query,
        k=5
    )

    docs = []

    for chunk_id, score in results:
        chunk = (
            db.query(Document)
            .filter(Document.id == chunk_id)
            .first()
        )

        docs.append(
            {
                "content": chunk.content,
                "score": score,
                "id": chunk.id
            }
        )           

    return docs

tools = [retrieve_knowledge]
