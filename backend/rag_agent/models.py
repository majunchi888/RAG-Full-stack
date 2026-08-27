from datetime import datetime

from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, DateTime, Integer, String, Text, JSON, ForeignKey, UniqueConstraint
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

# class UserDocument(Base):

#     __tablename__="user_documents"

#     id = Column(
#         Integer,
#         primary_key=True
#     )

#     filename = Column(
#         String
#     )


# class Document(Base):

#     __tablename__ = "documents"

#     id = Column(
#         Integer,
#         primary_key=True,
#         autoincrement=True
#     )


#     doc_id = Column(String)


#     content = Column(Text)


#     metadata_ = Column("metadata", JSON)


#     embedding = Column(Vector(1024))

# class Conversation(Base):
#     __tablename__ = "conversations"

#     id = Column(Integer, primary_key=True, autoincrement=True)

#     user_id = Column(
#         Integer,
#         nullable=False,
#         index=True
#     )

#     title = Column(
#         String(200),
#         default="新聊天"
#     )

#     created_at = Column(
#         DateTime,
#         default=datetime.utcnow
#     )

# # 中间表
# class ConversationDocument(Base):
#     __tablename__ = "conversation_documents"

#     id = Column(Integer, primary_key=True, autoincrement=True)

#     conversation_id = Column(
#         Integer,
#         ForeignKey("conversations.id"),
#         nullable=False
#     )

#     document_doc_id = Column(
#         Integer,
#         nullable=False
#     )

# # 短期记忆
# class Message(Base):
#     __tablename__ = "messages"

#     id = Column(Integer, primary_key=True)

#     conversation_id = Column(
#         Integer,
#         ForeignKey("conversations.id"),
#         nullable=False
#     )

#     role = Column(
#         String,
#         nullable=False
#     )

#     content = Column(
#         Text,
#         nullable=False
#     )

#     created_at = Column(
#         DateTime,
#         default=datetime.utcnow
#     )



class UserDocument(Base):
    """用户上传的原始文件/URL 记录（逻辑文档）"""
    __tablename__ = "user_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    filename = Column(String(512), nullable=False)
    file_path = Column(String(1024), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="user_document", cascade="all, delete-orphan")
    conversation_documents = relationship("ConversationDocument", back_populates="user_document")


class Document(Base):
    """文档切片（检索最小单位）"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_document_id = Column(
        Integer,
        ForeignKey("user_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSON)
    embedding = Column(Vector(1024))
    created_at = Column(DateTime, default=datetime.utcnow)

    user_document = relationship("UserDocument", back_populates="documents")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String(200), default="新聊天")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversation_documents = relationship(
        "ConversationDocument",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )


class ConversationDocument(Base):
    """会话与逻辑文档的关联表（一个会话关联一个 UserDocument 只存一条）"""
    __tablename__ = "conversation_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_document_id = Column(
        Integer,
        ForeignKey("user_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("conversation_id", "user_document_id", name="uq_conversation_user_document"),
    )

    conversation = relationship("Conversation", back_populates="conversation_documents")
    user_document = relationship("UserDocument", back_populates="conversation_documents")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

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