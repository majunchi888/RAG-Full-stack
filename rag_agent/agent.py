from langchain.agents import create_agent
from rag_agent.llm import llm
from rag_agent.tools import tools
from langgraph.checkpoint.memory import InMemorySaver

system_prompt = """你是一个严格的 RAG Agent。
规则：
1. 必须使用 retrieve_knowledge 工具获取信息。
2. 仅基于工具返回的内容组织答案。
3. 回答时必须标注 [来自知识库]。
4. 回答清晰、简洁、专业。"""

agent_executor = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt,
    checkpointer=InMemorySaver(),
)
