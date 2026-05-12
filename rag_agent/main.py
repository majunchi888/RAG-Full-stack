from fastapi import FastAPI, UploadFile, File, Query
from typing import List
import os

from rag_agent.pydantic_model import ChatRequest, UploadResponse
from rag_agent.agent import agent_executor
from rag_agent.retriever import retriever, deduplicate_docs
from rag_agent.loaders import load_file
from rag_agent.vectorstore import vectorstore
from langchain_text_splitters import RecursiveCharacterTextSplitter

app = FastAPI(title="Agentic RAG - Chroma + 阿里云百炼")

@app.post("/chat")
async def chat(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    result = agent_executor.invoke(
        {"messages": [("human", request.question)]},
        config,
        verbose=True
    )
    final_answer = result["messages"][-1].content

    docs = retriever.invoke(request.question)
    unique_docs = deduplicate_docs(docs)

    sources = [
        {
            "source": doc.metadata.get("source"),
            "page": doc.metadata.get("page"),
        }
        for doc in unique_docs
    ]

    return {
        "question": request.question,
        "answer": final_answer,
        "sources": sources
    }

@app.post("/upload", response_model=UploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    """上传文档到知识库"""
    all_docs = []
    for file in files:
        temp_path = f"./temp_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        docs = load_file(file, temp_path)
        all_docs.extend(docs)

    # 分割文档
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = text_splitter.split_documents(all_docs)

    # 存入向量库
    if splits:
        vectorstore.add_documents(documents=splits)

    return {
        "message": f"成功上传并向量化 {len(splits)} 个文档片段！",
        "num_docs": len(splits)
    }

@app.get("/")
async def home():
    return {
        "message": "Agentic RAG 已启动！",
        "docs": "访问 /docs 测试接口"
    }

@app.delete("/delete")
async def delete_document(source: str = Query(..., description="文档来源文件名")):
    """
    删除指定文档（根据 source 字段）
    """
    try:
        vectorstore.delete(where={"source": source}) #where 是向量数据库（VectorStore）提供的过滤删除条件，按元数据（metadata）进行精准删除
        return {"message": f"文档 {source} 已删除"}
    except Exception as e:
        return {"error": str(e)}    