<div align="center">

# 🚀 Intelligent RAG Knowledge Base

**基于 FastAPI + React + PostgreSQL/pgvector + LangChain 的智能知识库问答系统**

多文档上传 · 混合检索 · 流式对话 · 长期记忆 · 容器化部署

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

---

## 📖 项目简介

本项目是一个端到端的 **RAG（检索增强生成）** 智能知识库问答系统。用户上传文档、音频/视频或网页链接后，系统自动完成解析、切分与向量化，并通过 **混合检索（BM25 + Dense）+ RRF 融合 + Cross-Encoder Rerank** 的多阶段链路，为用户的提问提供**带有来源引用**的流式回答。

同时内置**短期对话记忆**与**用户长期记忆**机制，让 AI 能够在多轮对话中记住上下文与用户偏好，实现更自然、连续的个性化问答体验。

## ✨ 核心特性

| 模块              | 特性                                                                                                                                                    |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 📄 **多格式解析** | 支持 PDF / DOCX / TXT 文档，MP3 / WAV / M4A 等音频，MP4 / MOV / MKV 等视频，以及 YouTube / Bilibili 视频链接，音视频自动转写（FunASR SenseVoice）后入库 |
| 🔍 **混合检索**   | BM25 稀疏检索 + BGE-M3 稠密向量检索双路召回，RRF 结果融合，Cohere Cross-Encoder 重排序，兼顾关键词精确匹配与语义理解                                    |
| 🧠 **双重记忆**   | 会话内短期记忆（多轮对话上下文）+ 用户长期记忆（LLM 自动提取身份/偏好/目标，按用户隔离）                                                                |
| ⚡ **流式对话**   | 基于 FastAPI SSE 的流式输出，逐 token 渲染，回答附带 Top-K 知识来源引用                                                                                 |
| 🗄️ **数据存储**   | PostgreSQL + pgvector 持久化用户、知识库、文档、Chunk、记忆数据，按用户/会话实现数据隔离                                                                |
| 📊 **RAG 评测**   | 集成 LangSmith，支持 Correctness / Relevance / Groundedness / Retrieval Relevance 等评测指标                                                            |
| 🐳 **一键部署**   | Backend + Frontend 双容器 Docker 化，HuggingFace 模型缓存，`docker compose up` 即可启动                                                                 |

---

## 🚀 快速开始

### 1️⃣ 前置条件

| 依赖           | 版本要求                      |
| -------------- | ----------------------------- |
| Python         | ≥ 3.11                        |
| Node.js        | ≥ 18                          |
| PostgreSQL     | 13+（需启用 `pgvector` 扩展） |
| Docker（可选） | 20.10+                        |

### 2️⃣ 克隆项目

```bash
git clone <your-repository-url>
cd rag_agent
```

### 3️⃣ 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
# ─── 阿里云百炼（LLM，OpenAI 兼容接口）───
ALIYUN_API_KEY=sk-xxxx
ALIYUN_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# ─── Cohere（Cross-Encoder 重排序）───
COHERE_API_KEY=xxxx

# ─── Tavily（网页检索，可选）───
TAVILY_API_KEY=xxxx

# ─── LangSmith（评测与追踪，可选）───
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=xxxx
LANGSMITH_PROJECT=rag-agent

# ─── PostgreSQL + pgvector ───
# Transaction mode（日常使用，推荐端口 6543）
DATABASE_URL=postgresql+psycopg2://user:password@localhost:6543/rag_db
# Session mode（迁移专用，端口 5432）
DIRECT_URL=postgresql://user:password@localhost:5432/rag_db
```

> 💡 需要确保数据库中已启用 pgvector 扩展：`CREATE EXTENSION IF NOT EXISTS vector;`

### 4️⃣ 启动后端

```bash
# 创建虚拟环境并安装依赖
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 启动 FastAPI 服务
uvicorn backend.rag_agent.main:app --reload
```

启动后访问 http://localhost:8000/docs 即可查看交互式 API 文档。

### 5️⃣ 启动前端

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 http://localhost 即可开始使用（开发服务器已将 `/api` 代理到后端 8000 端口）。

### 6️⃣ Docker 一键部署

```bash
docker compose up --build
```

| 服务     | 容器端口 | 宿主机端口 | 说明                                       |
| -------- | -------- | ---------- | ------------------------------------------ |
| backend  | 8080     | 8080       | FastAPI 后端（Nginx 通过容器网络代理）     |
| frontend | 80       | 5173       | Nginx 静态站点，访问 http://localhost:5173 |

---

## 🏗️ 系统架构

```text
                         ┌────────────────────────┐
                         │     React 前端          │
                         │   TailwindCSS / SSE     │
                         └───────┬─────────┬──────┘
                                 │         │
                        知识库管理  │         │  流式对话
                      (Upload/URL)│         │  (SSE Token)
                                 │         │
                         ┌───────┴─────────┴──────┐
                         │      FastAPI 后端        │
                         └───┬───────┬─────────┬───┘
                             │       │         │
                     ┌───────┴──┐ ┌──┴───────┐ ┌┴───────────┐
                     │ 文档流水线 │ │ 记忆模块  │ │ RAG 检索链路 │
                     └─┬─────┬──┘ └──┬───────┘ └─┬─────────┬─┘
                       │     │       │           │         │
                  文档/音视频  URL   短期记忆    BM25    BGE-M3 Dense
                   (FunASR)   │   长期记忆       │         │
                       │     │       │           └────┬────┘
                       └─────┴───────┘                │
                             │                      RRF 融合
                          Chunking                    │
                             │                   Cohere Rerank
                             └────────────┬───────────┘
                                          ↓
                             PostgreSQL + pgvector
                                          │
                                          ↓
                              ┌─────────────────────┐
                              │   LLM（Qwen，流式）   │
                              └─────────────────────┘
                                          │
                                          ↓
                                  Answer + Sources
```

## 🔍 RAG 检索链路

一条用户查询经过的完整处理流程：

```text
  User Query
      │
      ▼
┌─────────────────────────────────────────────┐
│             双路召回 (Recall)                │
│  ┌────────────────┐    ┌─────────────────┐  │
│  │  BM25 稀疏检索   │    │ BGE-M3 稠密检索 │  │
│  │ (关键词精确匹配)  │    │  (语义向量匹配)   │  │
│  └────────────────┘    └─────────────────┘  │
└──────────────────────┬──────────────────────┘
                       ▼
┌─────────────────────────────────────────────┐
│        RRF 融合 (Reciprocal Rank Fusion)     │
│      score(d) = Σ 1/(k + rankᵢ(d))，k=60     │
│          合并多路结果，生成候选集              │
└──────────────────────┬──────────────────────┘
                       ▼
┌─────────────────────────────────────────────┐
│      Cohere Cross-Encoder Rerank 重排序      │
│          对「查询-候选」对精细打分             │
└──────────────────────┬──────────────────────┘
                       ▼
                     Top-K Chunks
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   短期对话记忆    长期用户记忆    检索上下文 Context
        └──────────────┼──────────────┘
                       ▼
                 LLM 流式生成 (Qwen)
                       ▼
              Answer + Sources 引用
```

## 📂 项目结构

```text
rag_agent/
├── backend/
│   ├── rag_agent/                    # 后端核心代码
│   │   ├── main.py                   # FastAPI 应用入口 & SSE 路由
│   │   ├── llm.py                    # LLM 集成（阿里云百炼 Qwen）
│   │   ├── retriever.py              # 混合检索器（BM25 + Dense + RRF + Rerank）
│   │   ├── source_loader.py          # 文档/音视频/URL 解析与切分
│   │   ├── database.py               # PostgreSQL + pgvector 数据访问
│   │   ├── memory.py                 # 短期/长期记忆管理
│   │   ├── models.py                 # SQLAlchemy 数据模型 & 向量维度定义
│   │   ├── pydantic_model.py         # 请求/响应 Pydantic 模型
│   │   └── tools.py                  # 工具函数
│   ├── Dockerfile.backend            # 后端容器镜像
│   └── requirements.txt              # Python 依赖
├── frontend/
│   ├── src/
│   │   ├── components/               # React 组件
│   │   │   ├── ChatMessage.jsx       # 消息气泡（Markdown 渲染）
│   │   │   ├── ChatInput.jsx         # 输入框
│   │   │   ├── ConversationSidebar.jsx  # 会话侧边栏
│   │   │   ├── DocumentPanel.jsx     # 文档管理面板
│   │   │   ├── KnowledgeBase.jsx     # 知识库视图
│   │   │   ├── ThreadList.jsx        # 会话列表
│   │   │   ├── UploadDialog.jsx      # 上传对话框
│   │   │   └── UploadZone.jsx        # 拖拽上传区
│   │   ├── api.js                    # API 调用层（SSE 解析）
│   │   └── App.jsx                   # 应用入口
│   ├── Dockerfile.frontend           # 前端构建（多阶段 + Nginx）
│   ├── nginx.conf                    # Nginx 反代配置
│   ├── vite.config.js                # Vite 配置（/api 代理）
│   └── package.json
├── evaluator.py                      # RAG 评测脚本（LangSmith）
├── rag_konwledge.md                  # RAG 技术原理文档
├── docker-compose.yml                # 容器编排
├── pyproject.toml                    # 项目元数据
└── requirements.txt                  # Python 依赖清单
```

## 📦 支持的文档格式

| 类别    | 格式                          | 处理方式                      |
| ------- | ----------------------------- | ----------------------------- |
| 📄 文档 | PDF、DOCX、TXT                | 直接解析文本并切分            |
| 🎵 音频 | MP3、WAV、M4A、FLAC、AAC、OGG | FFmpeg 转换 → SenseVoice 转写 |
| 🎬 视频 | MP4、AVI、MOV、MKV、WEBM      | 提取音轨 → 转写               |
| 🔗 网页 | YouTube、Bilibili 视频链接    | yt-dlp 下载音频 → 转写        |

> 文档切分采用 `RecursiveCharacterTextSplitter`（默认 chunk_size=200，overlap=20）。

## 🗄️ 数据模型

| 表                       | 说明                       | 关键字段                                              |
| ------------------------ | -------------------------- | ----------------------------------------------------- |
| `users`                  | 用户（当前固定 user_id=1） | id                                                    |
| `conversations`          | 会话                       | id、user_id、title、created_at                        |
| `user_documents`         | 用户上传的文档记录         | id、filename                                          |
| `documents`              | 切分后的 Chunk（含向量）   | id、doc_id、content、metadata、embedding(Vector 1024) |
| `conversation_documents` | 会话与文档关联（数据隔离） | conversation_id、document_doc_id                      |
| `messages`               | 短期记忆（对话历史）       | conversation_id、role、content、created_at            |
| `user_memories`          | 长期记忆（用户偏好）       | user_id、key、value、updated_at                       |

## 🔌 API 参考

| 方法   | 路径                          | 说明                                                      |
| ------ | ----------------------------- | --------------------------------------------------------- |
| `GET`  | `/`                           | 健康检查，返回服务状态                                    |
| `POST` | `/conversations`              | 创建新会话，返回 `conversation_id`                        |
| `POST` | `/chat`                       | 流式对话（JSON: `query`, `conversation_id`），返回 SSE 流 |
| `POST` | `/conversations/{id}/sources` | 添加知识源（multipart 文件 或 `url` 表单字段）            |

### SSE 事件格式

`/chat` 接口通过 `text/event-stream` 推送以下事件：

```jsonc
// 1. 检索来源（回答前先返回引用）
data: {"type": "sources", "sources": [{"id": 1, "score": 0.87, "content": "..."}]}

// 2. 逐 token 流式内容
data: {"type": "token", "content": "这是"}

// 3. 生成完成
data: {"type": "done"}

// 4. 发生错误
data: {"type": "error", "message": "错误详情"}
```

## 🧠 记忆机制

- **短期记忆**：会话内的历史 `Message` 自动作为上下文拼接，支撑多轮连续对话。
- **长期记忆**：对话结束后，LLM 自动提取用户身份、偏好、目标等稳定信息，以键值对形式存入 `user_memories`，下次对话自动注入提示词，实现跨会话的用户个性化记忆。

## 📊 RAG 评测

项目集成 LangSmith 评测体系（`evaluator.py`），支持指标：

- **Correctness**：回答与参考答案的语义一致性
- **Relevance**：回答对提问的相关程度
- **Groundedness**：回答是否忠实于检索上下文（防幻觉）
- **Retrieval Relevance**：检索文档与问题的相关性

可通过对比「仅 Dense」与「BM25 + Dense + RRF + Rerank」的指标差异，量化混合检索的优化效果。

## 🛠️ 技术栈

| 层级     | 技术                                              |
| -------- | ------------------------------------------------- |
| 后端框架 | Python · FastAPI · LangChain · LangGraph          |
| 检索     | BGE-M3（Embedding） · BM25s · RRF · Cohere Rerank |
| 大模型   | 阿里云百炼 Qwen（OpenAI 兼容接口） · DashScope    |
| 音视频   | FunASR SenseVoice · FFmpeg · yt-dlp               |
| 数据存储 | PostgreSQL · pgvector · SQLAlchemy                |
| 前端     | React 18 · Vite 6 · TailwindCSS · SSE             |
| 评测     | LangSmith                                         |
| 部署     | Docker · Docker Compose · Nginx                   |

---

## 📄 相关文档

- [RAG 技术原理详解](rag_konwledge.md) —— 混合检索、RRF、Rerank、评测指标等基础知识

## 📝 License

本项目仅供学习与研究使用。
