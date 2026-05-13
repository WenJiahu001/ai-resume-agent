# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## 项目概述

AI 简历助手（"简历导航员"）—— 一个基于 LangGraph ReAct Agent 的智能面试助理。项目已重构为**前后端分离架构**，Agent 通过本地知识读取工具（读取数据层存放的简历 `.md` 文件）提供信息，并使用 SSE (Server-Sent Events) 流式响应面试官提问。为简化部署和测试，项目已移除原有的 RAG 向量数据库机制。

## 目录结构

- `backend/`：FastAPI 后端服务代码，使用 uv 进行包管理。
- `frontend_v2/`：Vue 3 前端工程代码，使用 Vite + npm，集成 Tailwind CSS。
- `data/`：存储用户不同模块的简历 Markdown 数据，供工具查询。

## 技术栈

- **后端**：Python 3.13, uv, FastAPI, LangGraph + LangChain, MySQL（存储用户数据和 LangGraph Checkpoint）
- **前端**：Vue 3 + Vite, TailwindCSS (v4), TypeScript, Pinia, Vue Router

## 常用开发命令

### 后端（需在项目根目录执行）

```bash
# 同步安装依赖
uv sync

# 启动开发服务器
uv run uvicorn app:app --app-dir backend --reload

# 初始化/迁移数据库表结构
uv run python backend/migrate_db.py

# 添加测试用户
uv run python backend/add_user.py
```

### 前端（需在 `frontend_v2` 目录执行）

```bash
cd frontend_v2

# 安装依赖
npm install

# 启动前端开发服务器
npm run dev

# 生产环境构建
npm run build
```

## 架构要点

### 1. 流式响应与线程通信
- 会话统一通过 `POST /api/chat/stream` 接入。
- `AgentService` 以单例模式持有 LangGraph Agent。
- 因为 `agent.stream()` 是同步阻塞逻辑，应用层面通过起一个 Python 背景**子线程** (Thread) 将大模型输出和执行工具结果逐块（chunk）放入内部队列 (Queue)，而在 FastAPI 的协程中非阻塞获取后转为 SSE 事件，前端按需渲染为打字机和工具调用的 UI 效果。

### 2. 工具和检索策略 (Skill based)
原本的向量查询架构已移除，现在使用基于系统文件路径匹配的 Tool `search_resume`：
- 分为 "个人信息"、"个人技能"、"工作经历"、"教育经历"、"项目经历" 等分类。
- 工具接收类目及关键字过滤，动态从 `data/` 目录中匹配特定 Markdown 文件组合后读取给大模型使用上下文。

### 3. 会话和消息裁剪
- 必须基于 `PyMySQLSaver` 将所有的对话记录保存到 MySQL `checkpoints` 表内。
- 为了防止大上下文引起耗时爆表和长度崩溃，由 LangGraph 的 `pre_model_hook` (位于 `services/agent.py`) 对输入消息内容提供 `filter_messages` 截断裁剪。
- 裁剪要保持：**最近 20 条**、始终保留顶部基础 **SystemMessage**、绝对不能将 **AI ToolCall 和外部 ToolMessage 拆分**（否则某些 API Provider 会直接报错）。

### 4. 环境与依赖
请参考根目录 `.env.example`。必须启动本地 MySQL 服务器并配置正确的 `DB_*` 变量。兼容 OpenAI 的大模型地址和 key 通过 `OPENAI_BASE_URL` 和 `OPENAI_API_KEY` 管理。