from pydoc import Doc

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from backend.rag_agent.models import ConversationDocument, UserDocument, Document, embedding_model

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

def create_user_document(filename):
    db = SessionLocal()

    doc = UserDocument(filename=filename)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    db.close()
    return doc.id

def insert_chunks(splits, doc_id, conversation_id):
    db = SessionLocal()

    try:
        texts = [doc.page_content for doc in splits]
    
        embeddings = embedding_model.encode(texts, normalize_embeddings=True)


        # 1. 插入所有 chunks
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            row = Document(
                doc_id=str(doc_id),
                content=text,
                metadata={"chunk_id": i},
                embedding=embedding.tolist()
            )
            db.add(row)

        db.flush()  # 先 flush，让数据库生成 id（但不提交）

        # 2. 建立会话与文档的关联
        # ---------- 一个会话关联一次逻辑文档（推荐） ----------
        relation = ConversationDocument(
            conversation_id=conversation_id,
            document_doc_id=doc_id          # 存逻辑 doc_id（text）
        )
        db.add(relation)

        # 3. 统一提交
        db.commit()
        print(f"成功插入 {len(texts)} 个 chunk，并关联到会话 {conversation_id}")

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


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