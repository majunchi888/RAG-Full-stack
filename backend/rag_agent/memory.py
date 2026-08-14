
from sqlalchemy.orm import Session

from backend.rag_agent import llm
from backend.rag_agent.models import UserMemory
from pydantic import BaseModel


class MemoryItem(BaseModel):
    key: str
    value: str

class MemoryResult(BaseModel):
    memories: list[MemoryItem]


# 保存用户长期记忆
def save_memory(
    db: Session,
    user_id: int,
    key: str,
    value: str
):
    memory = (
        db.query(UserMemory)
        .filter(
            UserMemory.user_id == user_id,
            UserMemory.key == key
        )
        .first()
    )

    if memory:
        memory.value = value
    else:
        memory = UserMemory(
            user_id=user_id,
            key=key,
            value=value
        )
        db.add(memory)

    db.commit()
    db.refresh(memory)

    return memory     

# 获取用户长期记忆
def get_memories(
    db: Session,
    user_id: int
):
    return (
        db.query(UserMemory)
        .filter(UserMemory.user_id == user_id)
        .order_by(UserMemory.updated_at.desc())
        .all()
    )
# 格式化
def format_memories(memories):
    if not memories:
        return "暂无长期记忆"

    return "\n".join(
        f"- {memory.key}: {memory.value}"
        for memory in memories
    )

# 提取长期记忆
def extract_memories(query: str, answer: str):
    prompt = f"""
            你负责提取用户值得长期保存的信息。
            
            只提取：
            - 用户身份信息
            - 用户长期目标
            - 用户长期偏好
            - 用户稳定的背景信息
            
            不要提取：
            - 一次性问题
            - 临时任务
            - 当前对话中的普通事实
            - 不确定的信息
            
            用户：
            {query}
            
            助手：
            {answer}
            
            请提取值得长期保存的信息。
            如果没有，返回空列表。
            """

    result = llm.with_structured_output(
        MemoryResult
    ).invoke(prompt)

    return result.memories