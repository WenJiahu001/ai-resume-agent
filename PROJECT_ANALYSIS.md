# 项目整体分析与发展建议报告

## 1. 当前项目现状评估

### 1.1 架构与技术栈
*   **后端**：基于 Python 3.13 + FastAPI，架构分层清晰（routes, services, models）。使用了前沿的 LangGraph 和 LangChain 构建 ReAct Agent，并实现了 MySQL 持久化 (Checkpoint) 和 SSE 流式响应，基础架构非常健壮。
*   **RAG 检索**：整合了 Qdrant 向量数据库，并使用 MMR 算法进行检索，简历数据按类目进行 metadata 过滤，设计合理。
*   **前端**：使用纯静态 HTML + Vue 3 CDN + Tailwind CSS CDN 实现，通过 JWT 认证与后端交互，快速实现了功能的闭环。

### 1.2 存在的痛点与缺失
*   **前端过于臃肿**：`frontend/index.html` 文件大小已达 50KB 左右，包含了所有的 UI、样式和交互逻辑。随着功能的进一步扩展（如上下文管理、多会话切换、侧边栏管理），单文件将极难维护。
*   **Token 追踪缺失**：正如当前的 `todo.md` 所述，缺乏对 LLM API 调用消耗的详细监控和统计。这对于成本规划和后续可能的多用户配额限制至关重要。
*   **RAG 颗粒度与质量**：目前使用的是重置式注入 (`/api/vector/ingest` 会清空集合)，且检索仅依赖基础的向量检索 + MMR。在遇到复杂的简历交互（比如“对比我的两段工作经历”）时，可能容易丢失细节。
*   **基础运维与部署缺失**：没有容器化（Docker）支持，启动流程依赖本地环境配置，不便于一键部署和迁移。
*   **Agent 能力较为单一**：现有工具只有向量检索和时间获取，Agent 能够执行的动作有限。

---

## 2. 接下来应该发展的方向与建议

### 方向一：前端工程化与体验升级（短期/高优先级）
1.  **重构前端项目**：放弃单文件模式，使用 **Vite + Vue 3 + TypeScript** 搭建标准前端工程。将聊天区域、侧边栏对话历史、用户设置拆分为独立的 Vue 组件。
2.  **状态管理**：使用 Pinia 管理用户状态（Token、用户信息）和会话状态。
3.  **UI 库引入**：可以使用 Naive UI 或 Element Plus 替换部分手写的 Tailwind UI，加速复杂组件（如弹窗、配置面板）的开发。

### 方向二：Token 统计与数据看板（短期/中优先级）
1.  **后端实现 Token 回调拦截**：在 LangChain/LangGraph 中注入自定义的 `CallbackHandler`，在每次 LLM 调用结束时提取 `usage_metadata`（Prompt Tokens, Completion Tokens）。
2.  **持久化追踪**：在 MySQL 中新建 `token_usage` 表，记录 `user_id`, `thread_id`, `prompt_tokens`, `completion_tokens`, `model_name` 和 `cost`。
3.  **前端展示**：在前端增加一个“统计看板”页面，让用户看到自己的 Token 消耗曲线和额度。

### 方向三：RAG 检索优化机制（中期/高优先级）
1.  **混合检索 (Hybrid Search)**：引入 BM25 全文检索，与现有的 Qdrant 密集向量检索结合，处理特定关键词（如特定公司名、生僻技术栈）的召回缺失问题。
2.  **Rerank 重排机制**：在检索出 Top K 文档后，引入本地/API 的 Reranker 模型（如 BGE-Reranker），根据当前 Prompt 对结果进行二次打分重排，提升输入给大模型的上下文准确度。
3.  **增量更新**：修改 `/api/vector/ingest`，支持基于文档 hash 的增量更新，而不是每次粗暴地清空重建。

### 方向四：Agent 能力扩展（中期/中优先级）
1.  **简历润色/评估工具**：添加新工具，接收用户的某段经历，运用专用 Prompt 返回优化建议。
2.  **简历导出**：增加一个能够将当前对话中生成的优质内容整合，并输出为 PDF 或 Markdown 文件提供下载的工具流程。
3.  **增加长期记忆槽**：现在的 LangGraph checkpoint 只是保留会话，可以进一步增加一个工具：在每轮对话结束后，提取关键信息（如用户目标、用户短板）持久化为“用户画像”，在下次对话时直接注入 System Prompt。

### 方向五：工程部署与 CI/CD（中长期/高优先级）
1.  **容器化 (Docker化)**：编写 `Dockerfile`（分别构建前后端），并使用 `docker-compose.yml` 统一编排 MySQL, Qdrant, Backend, Frontend。
2.  **环境变量解耦**：将前端访问的 API Base URL 等彻底解耦为构建期/运行期环境变量。

---

## 3. 接下来几步的具体执行建议

1.  **第一步**：优先完成 `todo.md` 中的 **[Token消耗情况详细]**。这能在后端修改少量代码（拦截 LLM 回调并写入数据库表）来迅速闭环一个实用功能。
2.  **第二步**：将当前庞大的 `index.html` 转化为 Vite 工程化项目，为后续复杂的 UI 变更打下基础。
3.  **第三步**：探索 Qdrant + BGE Reranker 优化 RAG 的召回效果。
