from sqlalchemy.orm import Session

from backend.rag_agent.database import get_memories, save_memory
from backend.rag_agent.models import Message, UserMemory

from backend.rag_agent.models import Base
from backend.rag_agent.database import engine   # ← 改成你真实的 engine 导入路径

print("正在创建表...")
Base.metadata.create_all(bind=engine)
print("创建完成！")