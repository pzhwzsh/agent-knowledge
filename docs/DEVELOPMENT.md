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

- 提交纯文本。
- 提交 URL。
- URL 抓取前进行 SSRF 防护。
- 使用 `httpx`、`trafilatura`、`BeautifulSoup` 提取网页正文。
- 按 hash 或 canonical URL 去重。
- 记录 ingestion job 状态。
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

- `process_ingestion_job`：处理已有 ingestion job。
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

最近通过结果：`pytest` 48 passed，`ruff check app` passed，前端 `npm run build` passed。

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
