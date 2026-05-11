from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from config import ALIYUN_API_KEY, PERSIST_DIRECTORY

embeddings = DashScopeEmbeddings(
    model="text-embedding-v3",
    dashscope_api_key=ALIYUN_API_KEY
)

vectorstore = Chroma(
    collection_name="rag_collection",
    embedding_function=embeddings,
    persist_directory=PERSIST_DIRECTORY,
)
