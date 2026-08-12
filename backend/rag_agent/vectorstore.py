# from langchain_chroma import Chroma
# from langchain_community.embeddings import DashScopeEmbeddings
# from rag_agent.config import ALIYUN_API_KEY, PERSIST_DIRECTORY

# embeddings = DashScopeEmbeddings(
#     model="text-embedding-v3",
#     dashscope_api_key=ALIYUN_API_KEY
# )

# vectorstore = Chroma(
#     collection_name="rag_collection",
#     embedding_function=embeddings,
#     persist_directory=PERSIST_DIRECTORY,
# )

from database import SessionLocal
from models import Document, embedding_model
from sentence_transformers import SentenceTransformer

def insert_documents(
    documents,  # 文档列表，每个元素是一段文本
):

    db = SessionLocal() # 创建数据库会话


    for i,text in enumerate(documents):

        vector = embedding_model.encode(    # 把文本编码成向量，并做归一化
            text,
            normalize_embeddings=True  
        )

        # 创建 Document 对象
        doc = Document(
            doc_id=f"doc_{i}",

            content=text,

            embedding=vector.tolist()  # 把 numpy 数组转成 list，存入向量字段
        )

        db.add(doc)  # 把对象添加到会话中（还没真正写入数据库）

    db.commit()  # 把会话中的对象写入数据库

    db.close()


if __name__ == "__main__": 
    from sentence_transformers import SentenceTransformer

    docs=[
    "LangChain is a framework for LLM.",
    "RAG combines retrieval and generation."
    ]
    
    
    model=SentenceTransformer(
        "BAAI/bge-m3"
    )
    
    
    insert_documents(
        docs,
        model
    )