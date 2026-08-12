from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey
from pgvector.sqlalchemy import Vector
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer(
    "BAAI/bge-m3"
)

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
    title = Column(String(255), nullable=True)    

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
