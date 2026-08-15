# 🚀 Intelligent RAG Knowledge Base

一个基于 **FastAPI + React + PostgreSQL/pgvector + LangChain** 构建的智能知识库问答系统。

项目支持用户上传多种类型的文档，并通过 **Hybrid Retrieval（BM25 + Dense）+ RRF + Cross-Encoder Rerank** 构建多阶段检索链路，同时结合短期/长期记忆，为用户提供基于个人知识库的连续对话能力。

## ✨ Features

- 📄 多格式文档解析
  - PDF
  - DOCX
  - TXT
  - URL
  - 视频 / 音频转写后进入知识库

- 🔍 多阶段 RAG 检索
  - Dense Retrieval
  - BM25 Sparse Retrieval
  - Reciprocal Rank Fusion (RRF)
  - Cross-Encoder Rerank

- 🧠 Memory
  - 短期对话记忆
  - 用户长期记忆
  - 基于用户 / 会话进行数据隔离

- 📊 RAG Evaluation
  - LangSmith Dataset
  - Correctness
  - Relevance
  - Groundedness
  - Retrieval Relevance

- ⚡ Streaming Chat
  - FastAPI SSE
  - LLM 流式输出
  - Sources 引用展示

- 🗄️ 数据存储
  - PostgreSQL
  - pgvector
  - 用户、知识库、文档、Chunk 等数据持久化

- 🐳 Docker
  - Backend Docker 化
  - HuggingFace 模型缓存
  - 支持容器化部署

---

## 🏗️ Architecture

```text
                         React Frontend
                              │
                ┌─────────────┴─────────────┐
                │                           │
          Knowledge Base                  Chat
                │                           │
         Upload / Manage             SSE Streaming
                │                           │
                └─────────────┬─────────────┘
                              │
                         FastAPI Backend
                              │
             ┌────────────────┼────────────────┐
             │                │                │
        Document          Memory              RAG
        Pipeline                             Pipeline
             │                │                │
      ┌──────┴──────┐    ┌────┴────┐     ┌────┴─────┐
      │             │    │         │     │          │
    PDF/DOCX     Video/Audio  Short  Long   BM25    Dense
      │             │    │         │     │          │
      └──────┬──────┘    └────┬────┘     └────┬─────┘
             │                │                │
             ↓                │               RRF
          Chunking            │                │
             │                │             Rerank
             └────────────────┼────────────────┤
                              ↓
                             LLM
                              │
                              ↓
                     Answer + Sources
## 📂 项目结构

```

## 🔍 RAG Pipeline

当前核心检索链路：

User Query
│
↓
Query
│
├───────────────┐
↓ ↓
BM25 Dense Retrieval
│ │
│ BGE-M3
│ │
└───────┬───────┘
↓
RRF
↓
Candidate Chunks
↓
Cross Encoder
Reranker
↓
Top-K
↓
Context
↓
LLM
↓
Answer + Sources

## 🛠️ Tech Stack

Backend
Python
FastAPI
LangChain
LangGraph
PostgreSQL
pgvector
Retrieval
BGE-M3
BM25
RRF
Cross-Encoder Reranker
LLM
Qwen / OpenAI-compatible LLM API
Frontend
React
JavaScript
SSE
Evaluation
LangSmith
Deployment
Docker
Docker Compose

rag_agent/
├── backend/
│ ├── rag_agent/
│ │ ├── main.py # FastAPI 应用入口
│ │ ├── llm.py # LLM 模型集成
│ │ ├── retriever.py # 检索器实现
│ │ ├── database.py # pgvector 管理
│ │ ├── memory.py # 对话记忆管理
│ │ ├── source_loader.py # 数据上传处理
│ │ └── models.py # 数据模型定义
│ ├── Dockerfile.backend
│ └── requirements.txt
├── frontend/
│ ├── src/
│ │ ├── components/ # React 组件
│ │ │ ├── ChatMessage.jsx
│ │ │ ├── ChatInput.jsx
│ │ │ ├── DocumentPanel.jsx
│ │ │ └── ...
│ │ ├── api.js # API 调用层
│ │ └── App.jsx
│ ├── Dockerfile.frontend
│ ├── vite.config.js
│ └── package.json
├── docker-compose.yml
└── pyproject.toml

````




## 🚀 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose（可选）
- UV 包管理器（推荐）

### 本地开发

**1. 启动后端服务**

```bash
# 安装依赖
uv pip install -r requirements.txt

# 启动 FastAPI 服务（8000 端口）
uv run uvicorn backend.rag_agent.main:app --reload
````

访问 API 文档：http://localhost:8000/docs

**2. 启动前端应用**

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器（5173 端口）
npm run dev
```

访问应用：http://localhost:5173

> 💡 Vite 已配置反向代理，`/api/*` 请求自动转发到后端，无需手动配置 CORS

### Docker 部署

```bash
# 启动完整服务栈
docker-compose up -d

# 查看服务状态
docker-compose ps

# 停止服务
docker-compose down
```

访问应用：http://localhost:5173

## 📡 API 使用示例

### 上传文档

```bash
curl -X POST "http://127.0.0.1:8000/upload" \
  -F "files=@document.pdf"
```

### 知识问答

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "文档中提到了什么内容？", "conversation_id": "uuid"}'
```

### 添加外部来源

```bash
curl -X POST "http://127.0.0.1:8000/conversations/{id}/sources" \
  -H "accept: application/json" \
  -F "url=https://example.com/video"
```

## 🎨 UI 功能说明

| 区域         | 功能                           |
| ------------ | ------------------------------ |
| **聊天区**   | 实时对话展示，支持流式输出     |
| **侧边栏**   | 对话历史管理、知识库切换       |
| **上传按钮** | 右上角批量上传文档（支持拖拽） |
| **来源卡片** | 每个回答下方显示引用的源文件   |
| **思考动画** | 加载中展示动画反馈             |

## 🔧 配置说明

### 环境变量

创建 `.env` 文件（后端根目录）：

```env
# LLM 配置
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4

# 或使用阿里 DashScope
DASHSCOPE_API_KEY=sk-xxx

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_db

# 服务配置
BACKEND_PORT=8000
FRONTEND_PORT=5173
```

## 📚 技术栈

### 后端

- **FastAPI** - 高性能 Web 框架
- **LangChain/LangGraph** - LLM 编排框架
- **ChromaDB** - 向量数据库
- **Pydantic** - 数据验证
- **Python-docx/pdfplumber** - 文档解析

### 前端

- **React 18** - UI 框架
- **Vite** - 构建工具
- **Tailwind CSS** - 样式框架
- **Axios** - HTTP 客户端

## 🐳 Docker 命令参考

```bash
# 构建镜像
docker-compose build

# 启动服务（后台运行）
docker-compose up -d

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 进入容器
docker-compose exec backend bash

# 清理资源
docker-compose down -v
```

## 🤝 常见问题

**Q: 前端无法连接后端？**  
A: 确保后端运行在 8000 端口。检查 `vite.config.js` 中的代理配置。

**Q: 文档上传失败？**  
A: 检查文件格式（支持 PDF/DOCX/TXT）和文件大小限制。

**Q: 向量检索效果不理想？**  
A: 调整 chunk 大小和重叠参数，考虑使用重排序模型优化排序。

## 📝 开发指南

- 后端热重载：使用 `--reload` 参数
- 前端热更新：Vite 自动刷新
- 数据库持久化：`chroma_db/` 目录
- API 文档：访问 `/docs` 端点

## 📄 许可证

MIT License
