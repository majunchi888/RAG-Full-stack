from langchain_openai import ChatOpenAI
from config import ALIYUN_API_KEY , ALIYUN_URL

llm = ChatOpenAI(
    model="qwen3.5-plus",
    base_url=ALIYUN_URL,
    api_key=ALIYUN_API_KEY,
    temperature=0.01,
    max_tokens=2048,
    streaming=True
)
