from datetime import datetime

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, DateTime, Integer, String, Text, JSON, ForeignKey
from pgvector.sqlalchemy import Vector


embedding_model = None

def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        from sentence_transformers import SentenceTransformer
        embedding_model = SentenceTransformer("BAAI/bge-m3")  # 把模型名填回去
        print("Embedding 模型加载完成")
    return embedding_model

Base = declarative_base()

class UserDocument(Base):

    __tablename__="user_documents"

    id = Column(
        Integer,
        primary_key=True
    )

    filename = Column(
        String
    )


class Document(Base):

    __tablename__ = "documents"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )


    doc_id = Column(String)


    content = Column(Text)


    metadata_ = Column("metadata", JSON)


    embedding = Column(Vector(1024))

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    title = Column(
        String(200),
        default="新聊天"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

# 中间表
class ConversationDocument(Base):
    __tablename__ = "conversation_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        nullable=False
    )

    document_doc_id = Column(
        Integer,
        nullable=False
    )

# 短期记忆
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        nullable=False
    )

    role = Column(
        String,
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

# 长期记忆
class UserMemory(Base):
    __tablename__ = "user_memories"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    key = Column(
        String(100),
        nullable=False
    )

    value = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )    