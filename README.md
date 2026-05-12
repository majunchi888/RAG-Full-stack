📘 RAG Full Stack
一个基于 FastAPI + LangChain + ChromaDB + React 的全栈 RAG 系统，支持文档上传、向量检索、Agent 推理与引用返回。

🚀 功能特性
文档上传（PDF / DOCX）

文档解析与向量化

ChromaDB 检索

LangChain / LangGraph Agent 推理

OpenAI / DashScope 多模型支持

前端 Chat UI（React + Vite）

Docker 一键部署

## 项目结构

RAG-Full-stack/
│── rag_agent/ # FastAPI 后端
│── frontend/ # React 前端
│── chroma_db/ # 向量库持久化
│── Dockerfile.backend
│── Dockerfile.frontend
│── docker-compose.yml
│── requirements.txt

uv init

uv venv

.venv\Scripts\activate

后端测试：
cd rag_agent

uvicorn rag_agent.main:app --reload --port 8080 打开 http://localhost:8080/docs 进行测试

curl.exe -X POST "http://127.0.0.1:8000/upload" -F "files=@CET6.pdf"

curl.exe -X POST "http://127.0.0.1:8080/upload" -F "files=@研究生个人简历.docx"

curl.exe -X POST "http://127.0.0.1:8080/chat" -H "Content-Type: application/json" -d '{\"question\":\"马俊驰的成绩？\"}'

运行！！

# 1. 启动后端（确保已经在 8000 端口运行）

cd d:/rag_agent
uvicorn rag_agent.main:app --reload

# 2. 另一个终端启动前端

cd d:/rag*agent/frontend
npm run dev
访问 http://localhost:5173 即可使用。Vite 代理会自动将 /api/* 请求转发到后端的 http://localhost:8000/\_，无需额外配置 CORS。

功能说明
功能 说明
上传文档 右上角按钮，支持 PDF/Word/TXT，支持多文件
知识问答 底部输入框，Enter 发送，聊天气泡展示
思考动画 加载时显示跳跃的「...」动画
来源展示 如果后端返回 sources 字段，会在回答下方用卡片形式显示
