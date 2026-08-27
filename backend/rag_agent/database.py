from pydoc import Doc

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from backend.rag_agent.models import ConversationDocument, UserDocument, Document, UserMemory, get_embedding_model

import os 
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  
    pool_recycle=300,  
    poolclass=NullPool,  
)


SessionLocal = sessionmaker(
    bind=engine
)


def create_user_document(db: Session, filename: str, user_id: int) -> UserDocument:
    """创建逻辑文档记录，返回 UserDocument 对象"""
    user_doc = UserDocument(
        user_id=user_id,
        filename=filename,
    )
    db.add(user_doc)
    db.commit()
    db.refresh(user_doc)
    return user_doc


def insert_chunks(
    db: Session,
    chunks,                    # List of documents from chunker (有 page_content)
    user_document_id: int,
    conversation_id: int,
):
    """
    插入所有切片，并建立「会话 ↔ 逻辑文档」关联（只插一条）
    """
    try:
        texts = [doc.page_content for doc in chunks]

        if not texts:
            return

        model = get_embedding_model()
        embeddings = model.encode(texts, normalize_embeddings=True)

        # 1. 批量插入切片
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            row = Document(
                user_document_id=user_document_id,
                content=text,
                metadata_={"chunk_id": i},
                embedding=embedding.tolist()
            )
            db.add(row)

        # 2. 建立会话与逻辑文档的关联（只存一条）
        # 先检查是否已存在，避免唯一约束冲突
        exists = (
            db.query(ConversationDocument)
            .filter(
                ConversationDocument.conversation_id == conversation_id,
                ConversationDocument.user_document_id == user_document_id
            )
            .first()
        )
        if not exists:
            relation = ConversationDocument(
                conversation_id=conversation_id,
                user_document_id=user_document_id
            )
            db.add(relation)

        db.commit()
        print(f"成功插入 {len(texts)} 个 chunk，并关联到会话 {conversation_id}")

    except Exception as e:
        db.rollback()
        raise e


def get_documents(db: Session): # 参数必须是 SQLAlchemy 的`Session`实例

    docs = (
        db.query(Document)
        .all()
    )

    return docs

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

