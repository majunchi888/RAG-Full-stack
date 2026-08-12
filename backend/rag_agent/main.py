import uuid
from fastapi import Depends, FastAPI, UploadFile, File, Query
from typing import List, Annotated
import os

from regex import D
from sqlalchemy.orm import Session

from backend.rag_agent import retriever
from backend.rag_agent.models import Document
from backend.rag_agent.pydantic_model import ChatRequest, UploadResponse
from backend.rag_agent.llm import generate_answer
from backend.rag_agent.retriever import HybridRetriever
from backend.rag_agent.loaders import load_file
from backend.rag_agent.database import create_user_document, insert_chunks, get_db
from langchain_text_splitters import RecursiveCharacterTextSplitter

app = FastAPI(title="Agentic RAG - Chroma + 阿里云百炼")

app.openapi_version = "3.0.3"


@app.get("/chat")
def chat(
    query: str,
    db: Annotated[Session, Depends(get_db)]
):
    retriever = HybridRetriever(
        db=db
    )

    docs = retriever.search(
        query,
        k=5
    )

    context = "\n\n".join(
        [
            doc["content"]
            for doc in docs
        ]
    )

    answer = generate_answer(
        query=query,
        context=context
    )

    return {
        "answer": answer,
        "sources": docs
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(..., description="上传文件")
):
    """上传文档到知识库"""
    total_chunks = 0
    file_count = 0

    for file in files:
        doc_id = create_user_document(file.filename)
        temp_path = f"./temp_{uuid.uuid4()}_{file.filename}"
        try:
            # 写入临时磁盘
            with open(temp_path, "wb") as f:
                f.write(await file.read())

            docs = load_file(temp_path) # 只传路径，不要传UploadFile对象

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            splits = splitter.split_documents(docs)
            insert_chunks(splits, doc_id)
            total_chunks += len(splits)
            file_count += 1
        finally:
            # 无论成功失败，清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    return {
        "message": f"成功上传 {file_count} 个文件，共 {total_chunks} 个chunks",
        "num_docs": file_count
    }

@app.get("/")
async def home():
    return {
        "message": "Agentic RAG 已启动！",
        "docs": "访问 /docs 测试接口"
    }

# @app.delete("/delete")
# async def delete_document(source: str = Query(..., description="文档来源文件名")):
#     """
#     删除指定文档（根据 source 字段）
#     """
#     try:
#         vectorstore.delete(where={"source": source}) #where 是向量数据库（VectorStore）提供的过滤删除条件，按元数据（metadata）进行精准删除
#         return {"message": f"文档 {source} 已删除"}
#     except Exception as e:
#         return {"error": str(e)}    