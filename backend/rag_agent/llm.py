import os
from httpx import stream
from openai import OpenAI, base_url
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    api_key=os.getenv("ALIYUN_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model_name="qwen3.7-",
    temperature=0.2
)

client = OpenAI(
    api_key=os.getenv("ALIYUN_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


def generate_answer_stream(
    query: str,
    context: str,
    history: str = "",
    memory_text: str = "",
):

    prompt = f"""
              你是一个智能助手。

              【用户长期记忆】
              {memory_text}
              
              【当前对话历史】
              {history}
              
              【知识库检索内容】
              {context}
              
              【当前问题】
              {query}
              
              请根据以上信息回答问题。
              
              注意：
              1. 长期记忆用于了解用户的稳定背景和偏好，当前问题和长期记忆没关系的话不做参考。
              2. 当前知识库内容优先用于回答事实性问题。
              3. 如果信息不足，不要编造。
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
            },
        ],
        temperature=0.2,
        stream = True
    )
    # 流式返回

    for chunk in response:

        if not chunk.choices:
            continue

        content = chunk.choices[0].delta.content

        if content:
            yield content