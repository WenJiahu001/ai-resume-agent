# AI 辅助编程规范 - 简历智能体系统 (AI Resume Agent)

本规范用于指导 AI 编程助手在此项目环境下的代码开发。如果你发现当前项目的修改与这些规则冲突，应当遵循以下规范为最高准则。

## 1. 核心技术栈说明

- **基础环境**：Python 3.13 进行后端开发。
- **依赖管理**：统一使用 `uv` 进行包管理。
- **后端服务**：FastAPI + Uvicorn 提供高性能、强类型的异步 HTTP 接口服务。
- **AI / 智能体核心**：LangGraph + LangChain，构建基于 ReAct 模式的具身智能体。
- **持久化层**：MySQL，承担业务表（用户、会话）存储及 LangGraph Session Checkpoint（基于 `PyMySQLSaver`）的数据落地功能。
- **前端架构**：向现代化前端进发：Vite + Vue 3 (Composition API) + TypeScript + TailwindCSS。

## 2. 系统机制与最佳实践

### 2.1 智能体交互架构设计 (Agent & ReAct)
- **状态维护**：以 `thread_id` 和 `user_id` 构成的复合主键在 MySQL 中持久化对话状态节点。
- **SSE 推送机制**：必须使用 Server-Sent Events (SSE) 协议推送内容到前端。流式响应通常分三种类型传输：`token` (纯文本输出)、`tool_call` (启动工具) 和 `tool_result` (工具返回)。
- **隔离的队列推送**：LangGraph 的 `agent.stream()` 默认为同步阻塞函数，必须封装在后台多线程（Thread）中使用 `queue.Queue` 非阻塞回传到异步的 `async def stream_chat` 生成器接口中。

### 2.2 上下文压缩与 Token 控制 (Context Window)
- **消息滑动窗口**：通过为 Agent 增加 `pre_model_hook` (例如现有的 `filter_messages` 方法) 来修剪历史列表。
- **关键帧保留规则**：
  1. **首尾一致**：强制剔除旧消息时，必须原封不动保留最早的一条 `SystemMessage`。
  2. **调用链完整性防割裂**：决不能发生 Tool Call （AI工具调用请求）和对应的 ToolMessage （工具执行结果）被强行分段截断的情况；若历史窗口刚好划在 ToolMessage 处，应前移指针丢弃不完整的调用环结。

### 2.3 简历数据读取 (Local Text Fetching)
- **纯文本化处理**：弃用复杂的 RAG (向量提取 + MMR 检索)，采取更为准确简单的方案 —— 利用 `@tool` 根据具体的简历切面类别 (如 “工作经历”、“教育经历”等)，读取本地 `data/` 目录下的 Markdown 源文件反馈给大模型直接理解。

## 3. 编码习惯与风格限定

### 3.1 严格类型注解与 Pydantic
- FastAPI 的接口与所有自定义 Pydantic `BaseModel`（如 Request/Response Schemas）**必须书写全面的 Python Type Hints**，避免任何动态宽泛变量 (`Any` / 不指明类型的 dict 等)。
- 服务的返回体要按照定义好的 `response.py` 结构 (`success()`, `_error_response()`) 封装。

### 3.2 项目分层解耦 (MVC)
- **`routes/`** 仅允许包含与网络请求协议解析相关的逻辑，参数检验及装载；**不要在 route 内直接书写冗长的业务处理。**
- **`services/`** 存放独立业务类或函数（如 `AgentService`, `TokenUsageService` 等）。如果是需要高开销初始化或长生命周期的功能模块，需包装成严格的单例模式或走 lru_cache。
- **`models.py / sql/`** 分别对应接口请求规范和底层的 SQL 建表规约。

### 3.3 环境配置最佳实践
- 采用 `.env` 做本地配置隐匿，使用 `config.py` 中的 `dataclass` 做类型承载。
- 服务中如需读取配置，只允许通过 `config.get_settings()`（单例形式缓存对象）读取其属性节点，禁止直接使用 `os.environ` 硬编码获取配置。
