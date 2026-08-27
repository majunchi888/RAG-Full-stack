import time
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
def create_conversation(db: Annotated[Session, Depends(get_db)]):
    t0 = time.time()

    conversation = Conversation(title="新聊天", user_id=1)  # 实际应从认证中获取真实 user_id
    db.add(conversation)

    t1 = time.time()
    db.commit()
    t2 = time.time()
    db.refresh(conversation)
    t3 = time.time()

    print(f"add: {t1-t0:.2f}s, commit: {t2-t1:.2f}s, refresh: {t3-t2:.2f}s, total: {t3-t0:.2f}s")

    return {
        "conversation_id": conversation.id,
        "title": conversation.title
    }


@app.post("/chat")
def chat(
    request: ChatRequest,
    db: Annotated[Session, Depends(get_db)]
):
    conversation_id = request.conversation_id
    query = request.query

    # 1. 校验会话
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="聊天不存在")

    user_id = conversation.user_id

    # 2. 短期记忆（最近4条）
    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .limit(4)
        .all()
    )

    messages = [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": query})

    # 3. 长期记忆
    memories = get_memories(db, user_id=user_id)
    memory_text = format_memories(memories)

    # 4. 混合检索（已适配新模型）
    retriever = HybridRetriever(db=db, conversation_id=conversation_id)
    docs = retriever.search(query, k=5)

    context = "\n\n".join([doc["content"] for doc in docs])

    # 5. 先保存用户消息
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=query
    )
    db.add(user_message)
    db.commit()

    # 6. SSE 流式响应
    def generate():
        full_answer = ""
        try:
            # 发送 sources
            yield f"data: {json.dumps({'type': 'sources', 'sources': docs}, ensure_ascii=False)}\n\n"

            # 流式生成答案
            for chunk in generate_answer_stream(
                query=query,
                context=context,
                history=messages,
                memory_text=memory_text
            ):
                full_answer += chunk
                yield f"data: {json.dumps({'type': 'token', 'content': chunk}, ensure_ascii=False)}\n\n"

            # 保存 AI 消息
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_answer
            )
            db.add(assistant_message)

            # 可选：提取并保存新记忆
            # new_memories = extract_memories(query, full_answer)
            # for memory in new_memories:
            #     save_memory(db=db, user_id=user_id, key=memory.key, value=memory.value)

            db.commit()

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            db.rollback()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/conversations/{conversation_id}/sources")
async def add_sources(
    conversation_id: int,
    db: Annotated[Session, Depends(get_db)],
    files: List[UploadFile] | None = File(default=None),
    url: str | None = Form(default=None),
):
    """向会话知识库添加文件或 URL"""

    if not files and not url:
        raise HTTPException(status_code=400, detail="请上传文件或提供 URL")

    # 校验会话是否存在
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="聊天不存在")

    total_chunks = 0
    sources = []

    # -------------------------
    # 处理文件上传
    # -------------------------
    for file in files or []:
        # 1. 创建 UserDocument 记录
        user_doc = create_user_document(
            db=db,
            filename=file.filename,
            user_id=conversation.user_id   # 关联到会话所属用户
        )

        temp_path = f"./temp_{uuid.uuid4()}_{file.filename}"

        try:
            # 保存临时文件
            content = await file.read()
            with open(temp_path, "wb") as f:
                f.write(content)

            # 2. 分块
            chunks = chunker.create_chunks(temp_path)

            # 3. 插入 Document + 建立 ConversationDocument 关联
            insert_chunks(
                db=db,
                chunks=chunks,
                user_document_id=user_doc.id,
                conversation_id=conversation_id
            )

            total_chunks += len(chunks)

            sources.append({
                "user_document_id": user_doc.id,
                "name": file.filename,
                "type": "file",
                "chunks": len(chunks),
            })

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    # -------------------------
    # 处理 URL
    # -------------------------
    if url:
        user_doc = create_user_document(
            db=db,
            filename=url,          # 用 URL 作为显示名称
            user_id=conversation.user_id
        )

        try:
            chunks = chunker.create_chunks(url)

            insert_chunks(
                db=db,
                chunks=chunks,
                user_document_id=user_doc.id,
                conversation_id=conversation_id
            )

            total_chunks += len(chunks)

            sources.append({
                "user_document_id": user_doc.id,
                "name": url,
                "type": "url",
                "chunks": len(chunks),
            })

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"URL处理失败: {str(e)}")

    return {
        "message": "知识源添加成功",
        "total_chunks": total_chunks,
        "sources": sources
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

