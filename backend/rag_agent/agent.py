from langchain.agents import create_agent
from backend.rag_agent.tools import tools
from backend.rag_agent.llm import llm
from langgraph.checkpoint.memory import InMemorySaver

system_prompt = """
你是一个基于本地知识库的智能问答助手（RAG）。

规则：
1. 优先使用 retrieve_knowledge 的内容回答问题
2. 只能基于知识库或确定的问题回答，不得编造
3. 如果知识库没有相关内容，直接回答：“知识库中未找到相关信息”
4. 知识库搜不到，大模型自己的回答,不要添加[来自知识库]
5. 回答要简洁、准确
"""


agent_executor = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt,
    checkpointer=InMemorySaver(),
)
