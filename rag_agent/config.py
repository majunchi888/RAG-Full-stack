import os
from dotenv import load_dotenv

load_dotenv()

# API 配置
ALIYUN_API_KEY = os.getenv("ALIYUN_API_KEY")
ALIYUN_URL = os.getenv("ALIYUN_URL")

# 向量数据库持久化目录
PERSIST_DIRECTORY = "./chroma_db"
