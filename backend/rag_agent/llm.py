from langchain_openai import ChatOpenAI
from rag_agent.config import ALIYUN_API_KEY , ALIYUN_URL

llm = ChatOpenAI(
    model="qwen3.6-plus",
    base_url=ALIYUN_URL,
    api_key=ALIYUN_API_KEY,
    temperature=0.1,
    max_tokens=2048,
    streaming=True
)
