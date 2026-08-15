import uuid
import json
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Annotated
import os
from sqlalchemy.orm import Session
from backend.rag_agent.source_loader import DocumentChunker 
from backend.rag_agent.models import Conversation, Message
from backend.rag_agent.pydantic_model import ChatRequest
from backend.rag_agent.llm import generate_answer_stream
from backend.rag_agent.retriever import HybridRetriever
from backend.rag_agent.database import create_user_document,  insert_chunks, get_db
from backend.rag_agent.memory import extract_memories, format_memories, get_memories, save_memory


chunker = DocumentChunker()

app = FastAPI(title="Agentic RAG - Chroma + 阿里云百炼")

app.openapi_version = "3.0.3"

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/conversations")
def create_conversation(
    db: Annotated[Session, Depends(get_db)]
):
    conversation = Conversation(
        title="新聊天",
        user_id=1
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {
        "conversation_id": conversation.id,
        "title": conversation.title
    }

@app.post("/chat")
def chat(
    # query: str,
    # conversation_id: int,
    request: ChatRequest,
    db: Annotated[Session, Depends(get_db)]
):
    conversation_id = request.conversation_id
    query = request.query

    # 用户 ID
    conversation = (
        db.query(Conversation)
            .filter(
                Conversation.id == conversation_id
            )
            .first()
        )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="聊天不存在"
        )

    user_id = conversation.user_id
    
    # 短期记忆
    history = (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation_id
        )
        .order_by(Message.created_at)
        .all()
    )

    messages = []

    for message in history:
        messages.append({
            "role": message.role,
            "content": message.content
        })

    messages.append({
        "role": "user",
        "content": query
    })

    # 长期记忆
    memories = get_memories(
    db,
    user_id=user_id
    )
    
    memory_text = format_memories(memories)
    
    # 检索回答
    retriever = HybridRetriever(
        db=db,
        conversation_id=conversation_id
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

    # 5. 保存聊天记录
    # 用户消息
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=query
    )

    db.add(user_message)
    db.commit()

    # AI 消息
    # SSE 流式响应
    def generate():
        full_answer = ""
        
        try:
            # 1. 先发送 sources
            yield f"data: {json.dumps({'type': 'sources', 'sources': docs}, ensure_ascii=False)}\n\n"
    
            # 2. 流式生成答案
            for chunk in generate_answer_stream(
                query=query,
                context=context,
                history=messages,
                memory_text=memory_text
            ):
                full_answer += chunk
                yield f"data: {json.dumps({'type': 'token', 'content': chunk}, ensure_ascii=False)}\n\n"
    
    
            # 4. 保存 AI 消息 + 更新记忆（放在 done 之后也可以）
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_answer
            )
            db.add(assistant_message)
            
            # new_memories = extract_memories(query, full_answer)
            # for memory in new_memories:
            #     save_memory(
            #         db=db,
            #         user_id=user_id,
            #         key=memory.key,
            #         value=memory.value
            #     )
            
            db.commit()
            # 3. 发送完成信号（先通知前端，再做耗时操作）
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            db.rollback()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
            # 注意：这里 yield 后最好不要再操作 db

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )        


# @app.post("/conversations/{conversation_id}/upload")
# async def upload_documents(
#     conversation_id: int,
#     db: Annotated[Session, Depends(get_db)],
#     files: List[UploadFile] = File(..., description="上传文件"),
# ):
#     """上传文档到知识库"""

#     conversation = (
#         db.query(Conversation)
#         .filter(Conversation.id == conversation_id)
#         .first()
#     )
    
#     if conversation is None:
#         raise HTTPException(
#             status_code=404,
#             detail="聊天不存在"
#         )

#     total_chunks = 0
#     file_count = 0

#     for file in files:
#         doc_id = create_user_document(file.filename)
#         temp_path = f"./temp_{uuid.uuid4()}_{file.filename}"
#         try:
#             # 写入临时磁盘
#             with open(temp_path, "wb") as f:
#                 f.write(await file.read())

#             docs = load_file(temp_path) # 只传路径，不要传UploadFile对象

#             splits = RecursiveCharacterTextSplitter(
#                 chunk_size=500,
#                 chunk_overlap=50
#             ).split_documents(docs)

#             insert_chunks(splits, doc_id, conversation_id)
#             total_chunks += len(splits)
#             file_count += 1
#         finally:
#             db.close()
#             # 无论成功失败，清理临时文件
#             if os.path.exists(temp_path):
#                 os.unlink(temp_path)

#     return {
#         "message": f"成功上传 {file_count} 个文件，共 {total_chunks} 个chunks",
#         "num_docs": file_count
#     }


@app.post("/conversations/{conversation_id}/sources")
async def add_sources(
    conversation_id: int,
    db: Annotated[Session, Depends(get_db)],
    files: list[UploadFile] | None = File(default=None),
    url: str | None = Form(default=None),
):
    """向会话知识库添加文件或 URL"""

    if not files and not url:
        raise HTTPException(
            status_code=400,
            detail="请上传文件或提供 URL"
        )

    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="聊天不存在"
        )

    if not files and not url:
        raise HTTPException(
            status_code=400,
            detail="请上传文件或提供 URL"
        )

    total_chunks = 0
    sources = []

    # -------------------------
    # 文件
    # -------------------------

    for file in files or []:

        doc_id = create_user_document(
            file.filename
        )

        temp_path = (
            f"./temp_{uuid.uuid4()}_{file.filename}"
        )

        try:
            with open(temp_path, "wb") as f:
                f.write(await file.read())

            chunks = chunker.create_chunks(
                temp_path
            )

            insert_chunks(
                chunks,
                doc_id,
                conversation_id
            )

            total_chunks += len(chunks)

            sources.append({
                "doc_id": doc_id,
                "name": file.filename,
                "type": "file",
                "chunks": len(chunks),
            })

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    # -------------------------
    # URL
    # -------------------------

    if url:

        doc_id = create_user_document(url)

        try:

            chunks = chunker.create_chunks(url)

            insert_chunks(
                chunks,
                doc_id,
                conversation_id
            )

            total_chunks += len(chunks)

            sources.append({
                "doc_id": doc_id,
                "name": url,
                "type": "url",
                "chunks": len(chunks),
            })

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"URL处理失败: {str(e)}"
            )

    return {
        "message": "知识源添加成功",
        "total_chunks": total_chunks,
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

