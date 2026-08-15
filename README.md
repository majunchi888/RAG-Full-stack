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

## 项目文档

```

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

```

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

```

---

## 🔍 RAG Pipeline

当前核心检索链路：

```
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
```

---

## 🛠️ Tech Stack

```
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
```

---

🚀 Quick Start

## 1. Clone

```
git clone git@github.com:majunchi888/RAG-Full-stack.git

cd your-repository
```

## 2. Configure Environment

```
Create .env:

LLM_API_KEY=your_api_key
DATABASE_URL=your_postgresql_url
LANGSMITH_API_KEY=your_langsmith_key
COHERE_API_KEY=your_cohere_key
```

## 3. Start Backend

```
cd backend

pip install -r requirements.txt

uvicorn rag_agent.main:app --host 0.0.0.0 --port 8000
```

## 4. Start Frontend

```
cd frontend

npm install
npm run dev
```

## 5. Docker

## docker compose up --build

## 💡 Example

```
用户上传：

论文.pdf
项目文档.docx
实验报告.pdf

系统完成：

Document Parsing
↓
Chunking
↓
Embedding
↓
PostgreSQL + pgvector

用户提问：

“实验中使用了什么模型？”

系统执行：

Query
↓
BM25 + Dense
↓
RRF
↓
Rerank
↓
Top-K Chunks
↓
LLM
↓
Answer

- Sources

最终返回带有知识库来源的回答。
```
