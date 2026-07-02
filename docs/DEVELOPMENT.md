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

- 更完整的任务监控告警、批量失败任务重放和生产运维面板。
- 更完整的推送模板、带签名退订链接、可配置频控和投递告警。
- 钉钉/邮件生产投递监控、失败告警和模板治理。
- 视频字幕总结。
- 浏览器插件。
- 基于用户反馈的推荐权重学习。
- 周报和月报。
- Rerank。
- 多模型路由。
- 文档导出。
- 完整管理后台仍未完成；当前只有反馈处理后台和审计日志查询第一版。
- token 成本统计。
- 前端更细的交互状态、更多业务细节页面和生产级体验打磨。

## 二期第一批收口状态

二期第一批已完成，重点是把一期 MVP 的核心链路从“能跑”推进到“更接近可运维、可验证、可交付”：

- 安全收口第一批：任务监控接口要求登录，URL 重定向后再次 SSRF 校验。
- 任务运维第一批：支持单个 failed ingestion job 人工重放。
- 推送控制第一批：支持禁用推送通道和当日成功推送频控。
- 前端工程化第一批：API timeout、AbortController、统一 ApiError、401 登录过期处理。
- 使用反馈闭环第一批：后端反馈 API、前端反馈维修台和用户隔离测试。
- 生产可复现第一批：前端依赖锁定，新增生产 compose override。
- 推荐模型化第一批：`RecommenderAgent` 接入 `ChatModel` 结构化推荐决策，保留规则 fallback。

二期第一批不等于完整生产商业化版本。使用反馈闭环已可记录后续需要维修或删除的功能。以下内容归入三期或生产化专项：浏览器插件、视频字幕总结、管理后台、token 成本统计、Rerank、多模型路由、文档导出、周报月报、批量任务运维、投递告警、审计日志完整落库、真实 provider 质量评估和 CI/CD。

## 已完成内容

### 基础设施

- 项目结构：`apps/api` 和 `apps/web`。
- Docker Compose 服务：`api`、`web`、`worker`、`postgres`、`redis`。
- PostgreSQL 使用 pgvector 镜像。
- FastAPI 应用和 `/health`。
- SQLAlchemy 2.x 基础配置。
- Alembic 初始迁移。
- structlog 基础日志配置。
- Celery app、worker、beat、核心业务任务入口、重试策略和管理员保护的基础监控接口已完成。

### 数据库模型

已建立模型和初始迁移：

- `users`（含 `is_admin` 管理员标记）
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
- `users.is_admin` 用于管理员权限基础。
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
- `POST /api/ingestions/{id}/replay`

已实现行为：

- 提交纯文本后创建 pending job，并投递 `process_ingestion_job` Celery 任务。
- 提交 URL 后创建 pending job，并投递 `process_ingestion_job` Celery 任务。
- `POST /api/ingestions` 返回 `202 Accepted`、job 和 Celery `task_id`；前端通过 `GET /api/ingestions/{id}` 或列表接口轮询状态。
- worker 处理时进行 URL SSRF 防护、抓取、解析、路由、摘要和 job 状态更新。
- 使用 `httpx`、`trafilatura`、`BeautifulSoup` 提取网页正文。
- 按 hash 或 canonical URL 去重。
- 记录 ingestion job 的 pending/running/success/failed 状态。
- 支持当前用户重放自己的 failed ingestion job，重放会清空错误、重置为 pending、retry_count 加 1 并重新投递 Celery。
- RouterAgent 路由。
- summary Agent 调用 `ChatModel` 生成结构化 JSON 摘要；模型输出异常时使用 fallback 基础摘要。
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
- 问答会先检索当前用户私有 chunks，再把片段作为上下文传给 `ChatModel` 生成答案。
- 问答返回 citations，便于回到原文档核对。
- RAG prompt 会限制问题、单片段和总上下文长度，并提示模型不要执行片段中的指令/提示词。
- `ChatModel` 调用失败时会返回带引用的降级答案，不让问答接口直接 500。
- 没有上下文时明确回答不知道。

### 推荐流程

已实现 API：

- `GET /api/recommendations`
- `POST /api/recommendations/generate`
- `POST /api/recommendations/{id}/ignore`
- `POST /api/recommendations/{id}/dislike`
- `POST /api/recommendations/{id}/save`

已实现行为：

- `RecommenderAgent` 会调用 `ChatModel` 输出结构化推荐决策，模型异常时回退到兴趣/负向关键词/分类规则评分。
- 推荐生成会读取当前用户历史 saved/disliked/ignored 推荐，对相似分类或标签做第一版反馈加权。
- 推荐默认进入 pending 状态。
- 保存推荐时才创建 document。
- 保存复用 document 入库幂等流程。

### 前端 UI

已实现：

- Next.js 前端已从占位页升级为多页面工作台，并接入后端 API。
- 左侧是带雷达扫描效果的创意登录区，已接入 `/api/auth/register`、`/api/auth/login` 和 `/api/auth/me`。
- 已实现 `/dashboard`、`/documents`、`/recommendations`、`/search`、`/preferences` 页面。
- API client 已支持默认超时、AbortController 信号合并、统一 `ApiError` 和 401 登录过期事件。
- 已接入 React Query Provider，`/dashboard` 和 `/recommendations` 已迁移到 `useQuery`/`useMutation`。
- 已适配 Tailwind CSS v4 的 PostCSS 插件配置。

尚未完成：其余页面 React Query 迁移、全局 toast/loading/error boundary、完整业务细节页、前端自动化测试、生产级体验打磨。

### 后台任务

已实现 Celery 任务入口：

- `process_ingestion_job`：处理已有 ingestion job；公开提交接口已投递这个任务，不再在请求内同步跑完整采集。
- `fetch_daily_sources`：抓取 GitHub Trending 并生成当前用户推荐。
- `generate_user_recommendations`：基于输入内容创建并处理 ingestion。
- `embed_document_chunks`：为已有文档 chunks 重新生成 embedding。
- `cleanup_failed_jobs`：将超时的 running/retrying job 标记为 failed。

这些任务复用现有 service，当前已覆盖测试。已配置 Celery Beat 定时调度、自动重试、worker 丢失拒收、prefetch 控制、每日推荐推送和需要登录访问的基础任务监控接口。尚未完成更完整的告警、人工重放和生产运维面板。

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
- `push_channel=disabled` 时会跳过推送并记录日志。
- 同一用户同一渠道当天已有 successful sent 日志时，会跳过重复推送并记录 skipped。

### 第十阶段：Ingestion 主链路异步化

本阶段已完成：

- `POST /api/ingestions` 从同步处理改为只创建 pending job 并投递 Celery。
- 返回结构新增 `task_id`，HTTP 状态码改为 `202 Accepted`。
- `GET /api/ingestions` 和 `GET /api/ingestions/{id}` 作为轮询入口。
- `IngestionProcessor.process_existing_job()` 保留为 worker 和内部测试使用，并支持字符串 UUID 边界输入。
- 前端 dashboard 快速采集已改为显示后台处理中状态，不再假设提交后立即生成 content。
- 后端测试已覆盖队列提交、worker 处理、用户隔离、文档/推荐/搜索下游链路。

### 第十一阶段：ChatModel RAG 接入

本阶段已完成：

- `SearchService.chat()` 不再直接拼接模板答案。
- 问答流程会先检索当前用户私有 chunks，再构造带引用编号的 RAG prompt。
- 通过 `get_chat_model()` 调用当前配置的 `ChatModel` 生成答案。
- 继续保留 citations 和 related_documents，方便用户核对来源。
- 测试已验证 ChatModel 会收到问题和检索片段。

仍需继续：真实 provider 环境下的质量评估、引用编号稳定性评估、召回评估和 rerank。

### 第十二阶段：结构化总结模型化

本阶段已完成：

- `GeneralAgent`、`GitHubAgent`、`LifestyleAgent` 已接入 `ChatModel`。
- 三类 Agent 会要求模型返回符合 Pydantic schema 的严格 JSON。
- 新增 JSON 解析和校验辅助逻辑，模型返回 Markdown fence 或纯 JSON 都可处理。
- 模型返回非 JSON 或字段不合规时，会使用 fallback 基础摘要，避免采集任务失败。
- 测试已覆盖模型 JSON 成功输出和 fallback 场景。

仍需继续：真实 provider 下的摘要质量评估、摘要 prompt 注入防护、摘要 token 长度控制、更稳定的输出格式约束，以及推荐质量评估。

### 第十三阶段：Docker Compose 最小集成验证脚本

本阶段已完成：

- 新增 `scripts/smoke_docker.ps1`。
- 脚本会启动 PostgreSQL、Redis、API、worker、beat。
- 脚本会等待 `/health`，执行 `alembic upgrade head`，检查 pgvector extension，并用登录 token 检查 `/api/tasks/schedule`。
- 脚本会注册测试用户、登录、提交异步 ingestion job，并轮询 job 到 success。
- 脚本会用登录 token 检查 `/api/tasks/health` 至少有一个 worker 在线。
- 提供 `-ValidateOnly` 模式用于只做脚本解析检查，不启动 Docker。

仍需继续：把该 smoke test 接入 CI，增加真实 provider 可选验证和更完整清理策略。

### 第十四阶段：安全收口第一批

本阶段已完成：

- `/api/tasks/health` 和 `/api/tasks/schedule` 已从公开接口改为需要登录访问。
- 任务监控接口测试新增未登录 401 和登录可访问的覆盖。
- `WebPageCollector` 会在请求完成后对 `response.url` 再次执行 SSRF 校验。
- 新增测试覆盖“初始公网 URL 重定向到 localhost/内网地址时拒绝访问”。

仍需继续：管理员后台、token 黑名单或服务端会话撤销、审计日志查询页面和更细权限分级。

### 第十五阶段：失败采集任务重放

本阶段已完成：

- 新增 `POST /api/ingestions/{id}/replay`。
- 仅允许当前用户重放自己的 failed ingestion job。
- 非 failed job 重放会返回 409。
- 重放会清空 `error_message` 和 `finished_at`，状态改为 pending，`retry_count` 加 1，并重新投递 `process_ingestion_job`。
- 已补充重放成功、非 failed 冲突和用户隔离测试。

仍需继续：更完整的任务运维面板、批量重放、失败原因聚合、重放审计日志和管理员权限模型。

### 第十六阶段：推送频控和禁用通道

本阶段已完成：

- `RecommendationPushService` 支持 `push_channel=disabled`，用于用户退订/禁用推荐推送。
- 已基于 `push_logs` 增加同一用户同一渠道的当日成功推送频控。
- 当天已经成功推送过时，后续触发会记录 skipped，避免重复打扰。
- 已补充禁用通道和频控测试。

仍需继续：邮件/钉钉模板打磨、带签名退订链接、投递失败告警、推送频控配置化和更完整的运营面板。

### 第十七阶段：前端 API client 工程化第一批

本阶段已完成：

- `apiRequest()` 增加默认 15 秒超时。
- 支持外部 `AbortSignal`，并与内部 timeout signal 合并。
- 新增 `ApiError`，携带 HTTP status 和请求 path。
- 401 响应会广播登录过期事件。
- `useAuth()` 监听登录过期事件并清理本地 token 和 user 状态。
- 前端 `npm run build` 已通过。

仍需继续：其余页面 React Query 迁移、全局 toast/loading/error boundary、页面级 skeleton、前端自动化测试。

### 第十八阶段：生产 Web 启动和依赖锁定

本阶段已完成：

- 前端 `package.json` 不再使用 `latest`，已按当前 lockfile 版本锁定主要依赖和 devDependencies。
- `package-lock.json` 已同步更新。
- 新增 `docker-compose.prod.yml`，用于生产模式覆盖：API 不开启 `--reload`，web 使用 `npm run build && npm run start`。
- 前端 `npm run build` 已通过。

仍需继续：npm audit 报告 2 个 moderate 漏洞，后续需要单独评估升级；生产镜像还可进一步改成多阶段构建以减小体积。

### 第十九阶段：推荐模型化第一批

本阶段已完成：

- `RecommenderAgent` 已接入 `ChatModel`。
- 模型需要返回符合 `RecommendationDecision` schema 的严格 JSON。
- 模型输出异常时保留原规则评分 fallback。
- 已补充模型推荐成功输出和 fallback 测试。

仍需继续：真实 provider 下的推荐质量评估、用户反馈学习、个性化权重调整、推荐去重和排序策略。

### 第二十阶段：RAG 生产质量增强第一批

本阶段已完成：

- `SearchService.chat()` 增加模型失败降级答案，保留 citations 和 related_documents。
- RAG prompt 增加上下文总长度、单片段长度和问题长度限制。
- RAG prompt 明确提示模型不要执行知识库片段中的指令、提示词或泄密要求。
- 已补充模型失败降级和上下文截断/注入防护提示测试。

仍需继续：真实 provider 质量评估、引用编号稳定性评估、召回评估、rerank 和人工测试反馈调优。

### 第二十一阶段：Docker Smoke 增强第一批

本阶段已完成：

- `scripts/smoke_docker.ps1` 已适配 `/api/tasks/schedule` 和 `/api/tasks/health` 的认证要求。
- smoke 会断言目标数据库已安装 pgvector extension。
- smoke 失败时会输出 `docker compose ps` 和 api/worker/beat/postgres/redis 最近日志，方便定位。
- `scripts/smoke_docker.ps1 -ValidateOnly` 已通过。

仍需继续：接入 CI、真实 provider 可选验证、完整清理策略和更细的失败产物归档。

### 第二十二阶段：管理员权限和审计日志基础

本阶段已完成：

- `users` 新增 `is_admin` 字段，并新增 Alembic migration。
- 新增 `get_current_admin_user` 依赖。
- 新增 `AuditLogRepository` 和 `AuditService`。
- `/api/tasks/health` 和 `/api/tasks/schedule` 升级为管理员访问，并记录 task monitor 查看审计日志。
- smoke 脚本会把临时 smoke 用户提升为 admin，用于验证管理员保护的 task 监控接口。
- 已补充普通用户 403、管理员访问和审计日志写入测试。

仍需继续：管理员后台、审计日志查询 API/UI、token 黑名单或服务端会话撤销、更细权限分级。

### 第二十三阶段：推荐反馈加权第一批

本阶段已完成：

- 推荐生成会读取当前用户历史 `saved`、`disliked`、`ignored` 记录。
- 与历史记录同分类或共享标签时，会根据用户反馈调整后续推荐分数。
- `saved` 相似内容加分，`disliked` 和 `ignored` 相似内容降分，并在 reason 中说明反馈调整。
- 已补充用户反馈影响后续推荐评分测试。

仍需继续：更完整的学习型推荐、时间衰减、反馈权重配置、重复内容去重、A/B 或人工质量评估。

### 第二十四阶段：React Query 工程化第一批

本阶段已完成：

- 新增 `app/providers.tsx`，在根 layout 注入 `QueryClientProvider`。
- 配置基础 query 默认值：`staleTime`、有限 retry、关闭 window focus 自动刷新。
- `/dashboard` 使用 `useQuery` 聚合文档、推荐和采集任务，并用 mutation 提交采集后 invalidate。
- `/recommendations` 使用 `useQuery` 加载推荐，用 mutation 处理 save/ignore/dislike 后 invalidate。
- 前端 `npm run build` 已通过。

仍需继续：documents/search/preferences 页面迁移、全局 toast、error boundary、页面 skeleton 和前端自动化测试。

### 第二十五阶段：使用反馈闭环第一批

本阶段已完成：

- 新增 `user_feedback` 私有表和 Alembic migration。
- 新增 `POST /api/feedback` 和 `GET /api/feedback`，只按当前用户读写。
- 反馈字段包含 feature、feedback_type、severity、message、status 和 metadata。
- 前端新增 `/feedback` 反馈维修台，并加入侧边栏导航。
- 反馈用于记录实际使用中要修、要删、出错或想增强的功能，为后续调试/维修/删减提供清单。
- 已补充反馈提交、列表和用户隔离测试。

仍需继续：更细的反馈分派、按反馈生成维修计划、与任务系统联动。

### 第二十六阶段：反馈处理后台第一批

本阶段已完成：

- 新增管理员接口 `GET /api/feedback/admin/all`，可查看全部用户反馈并按 status 筛选。
- 新增管理员接口 `PATCH /api/feedback/admin/{id}`，支持将反馈状态改为 open/planned/in_progress/resolved/wont_fix/deleted。
- 管理员查看和更新反馈会写入 `AuditLog`，便于后续追踪谁处理了哪些反馈。
- 前端新增 `/admin/feedback` 反馈处理后台，只有 `is_admin` 用户侧边栏显示入口。
- 已补充管理员可查看/更新、普通用户 403 和审计日志写入测试。

仍需继续：完整管理员后台、反馈负责人/优先级/处理备注、由反馈生成维修任务、审计导出和风险告警。

### 第二十七阶段：审计日志查询第一批

本阶段已完成：

- 新增管理员接口 `GET /api/audit/logs`，支持按 user_id、action 和 resource_type 筛选审计日志。
- 查询审计日志本身也会写入 `audit_log_list` 审计记录。
- 前端新增 `/admin/audit` 审计日志页面，只有 `is_admin` 用户侧边栏显示入口。
- 已补充管理员查询、筛选和普通用户 403 测试。

仍需继续：审计日志导出、按风险级别筛选、敏感操作告警、审计日志保留周期和更完整管理员后台。

### 第二十八阶段：服务端登出撤销第一批

本阶段已完成：

- 新生成的 JWT 增加 `jti` 标识。
- 新增 `revoked_tokens` 表和 Alembic migration，用于记录已登出的 token。
- `POST /api/auth/logout` 不再只是空响应，会把当前 token 的 `jti` 写入撤销表。
- `get_current_user` 会拒绝已撤销 token。
- 前端 `signOut()` 会先调用后端登出接口，再清除本地 token；接口失败也会清本地状态。
- 已补充登出后旧 token 访问 `/api/auth/me` 返回 401 的测试。

兼容说明：升级前已经签发、没有 `jti` 的旧 token 仍按旧逻辑校验，避免部署后把所有已登录用户立即踢下线；它们自然过期后，新 token 都会进入可撤销机制。

仍需继续：刷新 token、全设备登出、会话列表 UI 和更细权限分级。

### 第二十九阶段：撤销 token 清理任务第一批

本阶段已完成：

- `RevokedTokenRepository` 新增 `delete_expired()`，按 `expires_at` 清理已经过期的撤销记录。
- Celery 新增 `cleanup_revoked_tokens` 任务，返回删除数量。
- Celery Beat 新增 `cleanup-revoked-tokens` 定时任务，复用现有 cleanup interval。
- 已补充任务测试，确认只删除过期 token，未过期撤销记录会保留。

仍需继续：按用户/设备维度的会话管理、全设备登出、清理指标和告警。

### 第三十阶段：全局 Toast 提示第一批

本阶段已完成：

- 新增 `components/ToastProvider.tsx`，提供 `ToastProvider` 和 `useToast()`。
- `app/providers.tsx` 在 React Query 外层接入全局 toast 容器。
- 登录/注册成功与失败改用全局 toast。
- `/dashboard` 快速采集提交、成功、失败提示改用全局 toast。
- `/recommendations` 保存/忽略/不感兴趣操作结果改用全局 toast。
- `/feedback` 反馈提交成功/失败改用全局 toast。

仍需继续：迁移 documents/search/preferences/admin 页面提示、统一 query error toast、error boundary、页面 skeleton 和前端自动化测试。

## 未完成内容

以下内容不要描述为已可用能力：

- 更完整的任务监控告警、批量失败任务重放和生产运维面板。
- 每日定时发现。
- 邮件真实发送需要 SMTP 配置；后续还需模板、带签名退订链接、可配置频控和投递告警。
- 钉钉/邮件生产投递监控、失败告警和模板治理。
- 前端更细的交互状态、更多业务细节页面和生产级体验打磨。
- 真实 GitHub API 集成。
- 视频/PDF 完整解析。
- 高级推荐算法。
- 完整管理后台仍未完成；当前只有反馈处理后台和审计日志查询第一版。
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
- feedback、管理员反馈处理和审计日志查询。

最近通过结果：本轮 `python -m pytest app/tests/test_tasks.py` 为 10 passed；本轮 `python -m pytest app/tests/test_feedback.py` 为 5 passed，`python -m pytest app/tests/test_audit.py` 为 3 passed；历史后端全量 `pytest` 为 59 passed；`ruff check app` passed；前端 `npm run build` passed；`npm install --package-lock-only` completed，但 npm audit 仍有 2 个 moderate 漏洞需后续治理。

## 外部分析核对与修补计划

用户提供的外部分析整体方向是对的：项目已经超过空项目阶段，但仍混合了真实能力、mock 能力、占位能力和生产化待办。后续开发必须收紧口径，不再把 mock 或半接入能力写成完整生产能力。

### 分析中准确的问题

以下问题仍然成立，需要优先修补：

- 推荐质量仍需收口：`RecommenderAgent` 已接入模型辅助决策并保留规则 fallback，且已增加用户反馈加权第一版；仍缺真实 provider 评估、时间衰减、去重排序和更完整学习型推荐。
- 集成验证仍需增强：Docker Compose smoke 脚本已补 task 认证、pgvector extension 断言和失败日志收集；仍缺 CI 接入、真实 provider 可选验证和完整清理策略。
- 安全收口还需继续：task health/schedule 已升级为管理员访问并写入审计日志，URL 重定向后 SSRF 已复查并加测试，反馈处理后台和审计日志查询第一版已完成；服务端登出撤销第一版已完成；仍缺完整管理员后台、刷新 token、全设备登出、审计导出/告警和更细权限分级。
- 前端工程质量还需继续补强：API client 已补 timeout、AbortController 和统一 401，React Query 已接入并迁移 dashboard/recommendations，全局 toast 第一批已完成；仍缺其余页面迁移、统一 loading/error boundary、页面级 skeleton 和前端自动化测试。
- 生产可复现仍需继续：前端依赖已锁定，已新增生产 compose override；仍需处理 npm audit 漏洞、多阶段镜像、CI 构建和部署环境差异。
- ORM 和 Alembic migration 类型口径需要复查：部分 list 字段 ORM 用 JSONB/JSON 兼容类型，历史迁移里使用 ARRAY(String)，需要在真实 PostgreSQL 上验证并统一。
- AuditLog 仍是模型占位，尚未形成完整审计写入链路。

### 分析中已经过期或已修补的点

以下说法在当前代码中已经部分或全部过期：

- 搜索问答中文乱码：`SearchService.chat()` 已修复为正常中文。
- Chat 模板拼接：`SearchService.chat()` 已改为检索后调用 `ChatModel` 生成答案，并继续返回 citations。
- Summary mock：`GeneralAgent`、`GitHubAgent`、`LifestyleAgent` 已改为调用 `ChatModel` 生成结构化 JSON，保留 fallback。
- pgvector 数据库侧排序：已新增 PostgreSQL pgvector cosine distance 排序，SQLite 测试环境自动回退到 Python 余弦相似度。
- 推送完全没完成：该说法已过期；已实现站内推送日志、邮件/钉钉发送服务、`POST /api/push/daily`、`GET /api/push/logs`、每日推荐推送 Celery 任务、禁用通道和当日成功推送频控；但生产模板、带签名退订链接、可配置频控和投递告警仍未完成。
- 前端只有演示台：已拆为 `/dashboard`、`/documents`、`/recommendations`、`/search`、`/preferences` 多页面工作台；但交互状态和工程质量仍需要打磨。

### 修补优先级

1. 文档口径修正：所有文档必须明确区分“真实能力 / mock 能力 / 占位能力 / 生产待办”。
2. RAG 评估增强：补真实 provider 集成验证、答案质量评估、引用编号稳定性评估、召回评估和 rerank。
3. 推荐质量增强：补真实 provider 推荐评估、时间衰减、去重排序、权重配置和更完整学习型推荐。
4. 集成验证增强：将 Docker smoke test 接入 CI，补真实 provider 可选验证、完整清理策略和失败产物归档。
5. 安全收口增强：增加管理员后台、token 黑名单或服务端会话撤销、审计日志查询 UI/API 和更细权限分级。
6. 前端工程化增强：迁移剩余页面到 React Query，补全局 toast/loading/error boundary、页面级 skeleton 和前端自动化测试。
7. 生产可复现增强：处理 npm audit 漏洞、多阶段镜像、CI 构建和部署环境差异。

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
