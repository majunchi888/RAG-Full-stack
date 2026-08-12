import os
from openai import OpenAI, base_url
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    api_key=os.getenv("ALIYUN_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model_name="qwen3.7-flash",
    temperature=0.2
)

client = OpenAI(
    api_key=os.getenv("ALIYUN_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


def generate_answer(
    query: str,
    context: str
):

    prompt = f"""
              你是一个专业的知识库助手。
              
              请根据下面提供的资料回答问题。
              如果资料中没有答案，请明确说不知道。
              不要编造信息。
              
              资料：
              {context}
              
              
              问题：
              {query}
              
              
              回答：
              """


    response = client.chat.completions.create(
        model="qwen3.7-plus",
        messages=[
            {
                "role": "system",
                "content": "你是一个严谨的RAG助手"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )
    return response.choices[0].message.content