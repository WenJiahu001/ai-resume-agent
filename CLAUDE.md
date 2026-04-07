# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

AI 简历助手（"简历导航员"）—— 一个基于 LangGraph ReAct Agent 的智能面试助理。Agent 通过 RAG（检索增强生成）从向量知识库中检索简历数据（个人信息、技能、工作/项目/教育经历、证书），以 SSE 流式响应面试官的提问。

## 技术栈

- **Python 3.13**，包管理使用 **uv**
- **FastAPI** + **Uvicorn**（后端 API）
- **LangGraph** + **LangChain**（ReAct Agent，checkpoint 持久化到 MySQL）
- **Qdrant** 向量数据库 + **OpenAI Embeddings**（RAG 检索）
- **MySQL**（用户/会话元数据 + LangGraph checkpoint）
- **JWT**（认证，passlib bcrypt 密码哈希）
- 前端为纯静态 HTML（Vue 3 CDN + Tailwind CSS CDN），由 FastAPI StaticFiles 挂载

## 常用命令

```bash
# 启动开发服务器（从项目根目录）
uv run uvicorn app:app --app-dir backend --reload

# 初始化简历知识库（启动后调用一次）
# GET http://localhost:8000/api/vector/ingest

# 添加用户（脚本）
uv run python backend/add_user.py

# 数据库迁移
uv run python backend/migrate_db.py

# 安装依赖
uv sync
```

## 架构要点

### 请求流程

1. 前端通过 JWT Bearer Token 认证 → `deps.py:get_current_user_id` 校验
2. `POST /api/chat/stream` 接收 `ChatRequest`（thread_id + message）
3. `AgentService`（单例）持有 LangGraph ReAct Agent，使用 `PyMySQLSaver` 做会话 checkpoint
4. Agent 配备两个工具：`search`（RAG 检索向量库）和 `getNowDateTime`
5. `stream_chat()` 通过 `agent.stream()` 输出 SSE 事件（token / tool_result / end / error）

### Agent 消息裁剪

`filter_messages` 作为 `pre_model_hook` 注入 Agent，保留最近 20 条消息，始终保留首条 SystemMessage，确保不切断工具调用序列（AI tool_calls + ToolMessage 成对保留）。裁剪结果写入 `llm_input_messages` 键，不影响原始历史。

### 向量知识库

- 简历数据存放在 `data/` 目录，按子目录分类（个人信息、个人技能、工作经历、教育经历、项目经历、证书）
- 子目录名作为文档的 `metadata.category`，Agent 的 `search` 工具通过 category 过滤检索
- `GET /api/vector/ingest` 会**清空重建**集合后重新导入所有文档
- 检索使用 MMR 算法（k=3, lambda_mult=0.5）

### 提示词管理

`backend/prompts/` 下按场景管理提示词，`__init__.py` 中 `SYSTEM_PROMPT` 指向当前活跃的提示词（默认 `RESUME_ASSISTANT_PROMPT`）。

### 配置

所有配置通过 `config.py` 中的 dataclass 集中管理，`get_settings()` 返回 lru_cache 单例。环境变量从 `.env` 加载，参考 `.env.example`。

### 数据库

MySQL 表结构在 `backend/sql/init_tables.sql`，应用启动时自动执行。业务表仅 `users` 和 `threads` 两张；会话消息内容由 LangGraph 的 checkpoint 表管理。

### API 路由

| 前缀 | 模块 | 说明 |
|------|------|------|
| `/api/auth` | `routes/auth.py` | 登录认证 |
| `/api/chat` | `routes/chat.py` | SSE 流式聊天 |
| `/api/thread` | `routes/thread.py` | 会话 CRUD |
| `/api/vector` | `routes/vector.py` | 向量库导入 |

### 外部依赖服务

- **MySQL**：用户数据 + LangGraph checkpoint
- **Qdrant**：向量存储（默认 `localhost:6333`）
- **OpenAI 兼容 API**：LLM 调用 + Embedding（默认指向智谱 GLM，通过 `OPENAI_BASE_URL` 配置）
