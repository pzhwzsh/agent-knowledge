# 开发文档

本文档记录项目阶段、已完成内容、未完成内容和开发约定。

重要规则：以后每次新增功能、修改 API、修改模型、修改后台任务、修改部署方式或测试策略，都必须同步更新本文档和 `docs/HANDOFF.md`。如果改动会影响用户理解或使用方式，也必须同步更新 `README.md`。

## 一期 MVP 范围

一期目标是做出一个可部署、多用户隔离、能完成个人知识管理核心流程的后端 MVP。

一期包含：

- 用户注册和登录。
- 用户偏好配置：兴趣、不感兴趣关键词、启用分类和推送相关字段。
- 手动提交 URL 和纯文本。
- URL 抓取和 SSRF 防护。
- RouterAgent 和 mock 摘要 Agent。
- 全局 `contents` 去重。
- 用户私有 `documents`。
- 文档切片到 `document_chunks`。
- embedding provider 抽象和 mock embedding。
- 语义搜索。
- 带引用问答。
- 推荐箱。
- 推荐保存、忽略、不感兴趣操作。
- GitHub Trending 和 RSS 发现。
- Docker Compose 本地部署。
- 覆盖核心流程和用户隔离的后端测试。

## 二期候选范围

二期建议在一期后端稳定后推进：

- 更完整的任务监控告警、失败任务人工重放和生产运维面板。
- 更完整的推送模板、退订、频控和投递告警。
- 钉钉/邮件真实发送配置和生产投递监控。
- 视频字幕总结。
- 浏览器插件。
- 基于用户反馈的推荐权重学习。
- 周报和月报。
- Rerank。
- 多模型路由。
- 文档导出。
- 管理后台。
- token 成本统计。
- 前端更细的交互状态、更多业务细节页面和生产级体验打磨。

## 已完成内容

### 基础设施

- 项目结构：`apps/api` 和 `apps/web`。
- Docker Compose 服务：`api`、`web`、`worker`、`postgres`、`redis`。
- PostgreSQL 使用 pgvector 镜像。
- FastAPI 应用和 `/health`。
- SQLAlchemy 2.x 基础配置。
- Alembic 初始迁移。
- structlog 基础日志配置。
- Celery app、worker、beat、核心业务任务入口、重试策略和基础监控接口已完成。

### 数据库模型

已建立模型和初始迁移：

- `users`
- `user_preferences`
- `sources`
- `contents`
- `recommendations`
- `documents`
- `document_chunks`
- `ingestion_jobs`
- `agent_runs`
- `push_logs`
- `audit_logs`

关键约束：

- 私有表包含 `user_id`。
- 私有查询必须按当前认证用户过滤。
- `documents` 对 `(user_id, content_id)` 做唯一约束，用于重复保存幂等。
- `contents` 是全局表，可被多个用户复用。

### 认证和偏好

已实现 API：

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/preferences`
- `PUT /api/preferences`

规则：

- 密码已 hash。
- JWT secret 来自环境变量。
- 后端不信任前端传入的 `user_id`。
- 当前用户从 JWT 中解析。

### LLM 和 Agent

已实现：

- `ChatModel`
- `EmbeddingModel`
- `AgentRunner`
- `PromptTemplate`
- `TokenUsageTracker`
- `MockChatModel`
- `MockEmbeddingModel`
- OpenAI Compatible provider 接口。
- DeepSeek 和 Qwen provider 选择逻辑。
- RouterAgent、GeneralAgent、LifestyleAgent、GitHubAgent、RecommenderAgent。

### Ingestion 流程

已实现 API：

- `POST /api/ingestions`
- `GET /api/ingestions`
- `GET /api/ingestions/{id}`

已实现行为：

- 提交纯文本后创建 pending job，并投递 `process_ingestion_job` Celery 任务。
- 提交 URL 后创建 pending job，并投递 `process_ingestion_job` Celery 任务。
- `POST /api/ingestions` 返回 `202 Accepted`、job 和 Celery `task_id`；前端通过 `GET /api/ingestions/{id}` 或列表接口轮询状态。
- worker 处理时进行 URL SSRF 防护、抓取、解析、路由、摘要和 job 状态更新。
- 使用 `httpx`、`trafilatura`、`BeautifulSoup` 提取网页正文。
- 按 hash 或 canonical URL 去重。
- 记录 ingestion job 的 pending/running/success/failed 状态。
- RouterAgent 路由。
- mock summary Agent 输出。
- 记录 agent run。

### 文档和切片

已实现 API：

- `GET /api/documents`
- `POST /api/documents/from-content`
- `GET /api/documents/{id}`
- `DELETE /api/documents/{id}`

已实现行为：

- 将全局 content 保存为当前用户私有 document。
- 同一用户重复保存同一 content 时复用已有 document。
- 文本切片。
- 生成 embedding 并写入 chunk。
- 文档详情返回 chunks。

### 搜索和问答

已实现 API：

- `POST /api/search`
- `POST /api/chat`

已实现行为：

- 对问题生成 embedding。
- 只检索当前用户自己的 chunks。
- PostgreSQL 使用 pgvector 数据库侧 cosine distance 排序；SQLite 测试环境回退到 Python 侧余弦相似度排序。
- 问答返回 citations。
- 没有上下文时明确回答不知道。

### 推荐流程

已实现 API：

- `GET /api/recommendations`
- `POST /api/recommendations/generate`
- `POST /api/recommendations/{id}/ignore`
- `POST /api/recommendations/{id}/dislike`
- `POST /api/recommendations/{id}/save`

已实现行为：

- 根据兴趣、不感兴趣关键词和分类做基础评分。
- 推荐默认进入 pending 状态。
- 保存推荐时才创建 document。
- 保存复用 document 入库幂等流程。

### 前端 UI

已实现：

- Next.js 前端已从占位页升级为多页面工作台，并接入后端 API。
- 左侧是带雷达扫描效果的创意登录区，已接入 `/api/auth/register`、`/api/auth/login` 和 `/api/auth/me`。
- 已实现 `/dashboard`、`/documents`、`/recommendations`、`/search`、`/preferences` 页面。
- 已适配 Tailwind CSS v4 的 PostCSS 插件配置。

尚未完成：更细的加载/错误状态、完整业务细节页、前端自动化测试、生产级体验打磨。

### 后台任务

已实现 Celery 任务入口：

- `process_ingestion_job`：处理已有 ingestion job；公开提交接口已投递这个任务，不再在请求内同步跑完整采集。
- `fetch_daily_sources`：抓取 GitHub Trending 并生成当前用户推荐。
- `generate_user_recommendations`：基于输入内容创建并处理 ingestion。
- `embed_document_chunks`：为已有文档 chunks 重新生成 embedding。
- `cleanup_failed_jobs`：将超时的 running/retrying job 标记为 failed。

这些任务复用现有 service，当前已覆盖测试。已配置 Celery Beat 定时调度、自动重试、worker 丢失拒收、prefetch 控制、每日推荐推送和基础任务监控接口。尚未完成更完整的告警、人工重放和生产运维面板。

### 外部发现

已实现 API：

- `POST /api/discovery/github-trending`
- `POST /api/discovery/rss`

已实现行为：

- GitHub Trending HTML 基础解析。
- RSS/Atom 基础解析。
- 发现候选内容写入 `contents`。
- 为当前用户生成推荐。
- 发现内容不会直接创建 document。

### 推送流程

已实现：

- `POST /api/push/daily`：当前用户手动触发每日推荐推送。
- `GET /api/push/logs`：查看当前用户推送日志。
- `push_daily_recommendations` Celery task：单用户每日推荐推送。
- `push_daily_recommendations_for_active_users` Celery Beat 批处理入口。
- `in_app` 渠道会写入站内推送日志。
- `email` 和 `dingtalk` 渠道支持真实发送，但需要配置 SMTP 或 webhook；配置缺失时会记录 skipped。

### 第十阶段：Ingestion 主链路异步化

本阶段已完成：

- `POST /api/ingestions` 从同步处理改为只创建 pending job 并投递 Celery。
- 返回结构新增 `task_id`，HTTP 状态码改为 `202 Accepted`。
- `GET /api/ingestions` 和 `GET /api/ingestions/{id}` 作为轮询入口。
- `IngestionProcessor.process_existing_job()` 保留为 worker 和内部测试使用，并支持字符串 UUID 边界输入。
- 前端 dashboard 快速采集已改为显示后台处理中状态，不再假设提交后立即生成 content。
- 后端测试已覆盖队列提交、worker 处理、用户隔离、文档/推荐/搜索下游链路。

## 未完成内容

以下内容不要描述为已可用能力：

- 更完整的任务监控告警、失败任务人工重放和生产运维面板。
- 每日定时发现。
- 邮件真实发送需要 SMTP 配置；后续还需模板、退订、频控和投递告警。
- 钉钉/邮件真实发送配置和生产投递监控。
- 前端更细的交互状态、更多业务细节页面和生产级体验打磨。
- 真实 GitHub API 集成。
- 视频/PDF 完整解析。
- 高级推荐算法。
- 管理后台。
- 数据导出。
- token 成本统计。
- 更细的 pgvector 参数调优、召回评估和重排策略。

## 测试现状

当前后端测试覆盖：

- 认证和偏好。
- domain 基础层。
- LLM providers。
- ingestion。
- documents 和 chunks。
- search 和 chat。
- recommendations。
- discovery。
- tasks。

最近通过结果：异步采集影响范围测试 `pytest app/tests/test_ingestions.py app/tests/test_documents_api.py app/tests/test_recommendations.py app/tests/test_search_chat.py app/tests/test_tasks.py` 为 25 passed；`ruff check app` passed。此前全量后端测试为 48 passed，前端 `npm run build` passed。

## 外部分析核对与修补计划

用户提供的外部分析整体方向是对的：项目已经超过空项目阶段，但仍混合了真实能力、mock 能力、占位能力和生产化待办。后续开发必须收紧口径，不再把 mock 或半接入能力写成完整生产能力。

### 分析中准确的问题

以下问题仍然成立，需要优先修补：

- Mock 边界不够清楚：`GeneralAgent` 仍是规则/截断式摘要，`RecommenderAgent` 仍是规则评分，不是真正模型推荐。
- Chat 仍不是真正 LLM RAG：当前 chat 是检索片段拼接模板，尚未调用 `ChatModel` 生成答案。
- 测试环境与真实环境仍有差异：当前测试主要是 SQLite + mock LLM + `Base.metadata.create_all()`，不能证明 Docker Compose、PostgreSQL、pgvector、Celery worker、真实 LLM provider 全链路可用。
- 安全收口还不完整：task health/schedule 当前未加认证；URL 抓取需要确认重定向后的地址也经过 SSRF 校验；前端 token 存 localStorage，登出只是本地删除 token。
- 前端工程质量还需补强：API client 缺 timeout、AbortController、统一 401、全局 toast/loading/error boundary，React Query 依赖存在但未实际使用。
- 生产部署仍偏开发态：前端依赖使用 `latest`，Docker Compose 中 web 使用 dev server，不是生产构建运行方式。
- ORM 和 Alembic migration 类型口径需要复查：部分 list 字段 ORM 用 JSONB/JSON 兼容类型，历史迁移里使用 ARRAY(String)，需要在真实 PostgreSQL 上验证并统一。
- AuditLog 仍是模型占位，尚未形成完整审计写入链路。

### 分析中已经过期或已修补的点

以下说法在当前代码中已经部分或全部过期：

- 搜索问答中文乱码：`SearchService.chat()` 已修复为正常中文。
- pgvector 数据库侧排序：已新增 PostgreSQL pgvector cosine distance 排序，SQLite 测试环境自动回退到 Python 余弦相似度。
- 推送完全没完成：已实现站内推送日志、邮件/钉钉发送服务、`POST /api/push/daily`、`GET /api/push/logs`、每日推荐推送 Celery 任务；但生产模板、退订、频控和投递告警仍未完成。
- 前端只有演示台：已拆为 `/dashboard`、`/documents`、`/recommendations`、`/search`、`/preferences` 多页面工作台；但交互状态和工程质量仍需要打磨。

### 修补优先级

1. 文档口径修正：所有文档必须明确区分“真实能力 / mock 能力 / 占位能力 / 生产待办”。
2. 真实 RAG：让 `SearchService.chat()` 调用 `ChatModel`，用检索片段构造 prompt，保留 citations。
3. 真实总结和推荐：将规则 summary/recommender 标注为 mock 或替换为 LLM provider 实现。
4. 集成验证：新增 Docker Compose/PostgreSQL/pgvector/Alembic/Celery 的最小集成验证脚本。
5. 安全收口：task 监控接口加认证或管理员保护；URL 重定向后再次校验；梳理 token 存储和登出策略。
6. 前端工程化：模块化 API client，补 timeout、统一 401、toast/loading/error boundary，并实际使用 React Query。
7. 生产可复现：锁定前端依赖版本，增加生产 web 启动方式。

## 开发规则

- Route 只调用 service，不写业务逻辑。
- Service 负责业务逻辑和事务边界。
- Repository 负责数据库访问。
- Agent 不直接写数据库。
- Collector 不直接写数据库。
- Task 只调度 service。
- 所有私有查询必须按当前认证用户过滤。
- 新增私有表必须包含 `user_id`。
- 修改私有数据相关逻辑时，必须补充或更新用户隔离测试。

## 文档同步规则

修改以下内容时，必须同步更新 `docs/DEVELOPMENT.md` 和 `docs/HANDOFF.md`：

- API 行为。
- 数据库模型或迁移。
- 后台任务行为。
- 部署步骤。
- 环境变量。
- Agent、LLM provider 或 collector 行为。
- 测试策略或测试命令。

如果用户需要知道该变化，也必须同步更新 `README.md`。
