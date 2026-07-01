# 交接文档

本文档用于项目交接。以后任何会影响行为、运行方式、API、测试、风险或下一步计划的代码变更，都必须同步更新本文档和 `docs/DEVELOPMENT.md`。

## 当前状态

本项目是一个多用户 AI 知识库平台。当前后端已支持认证、偏好、内容提交、文档入库、搜索、带引用问答、推荐箱和 GitHub/RSS 发现；前端已接入后端认证、token 保存、仪表盘、文档、推荐箱、搜索问答、偏好设置和快速采集。

当前状态：二期第一批已收口，项目具备更稳的安全、任务运维、推送控制、前端 API client、生产 compose 和模型辅助推荐能力。

当前主要缺口已经进入三期/生产化专项：

- 更完整的任务监控告警、批量失败任务重放和生产运维面板。
- 更完整的推送模板、带签名退订链接、可配置频控和投递告警。
- React Query、全局 toast/loading/error boundary、前端自动化测试和生产级体验打磨。
- 浏览器插件、视频字幕总结、管理后台、Rerank、多模型路由、文档导出、token 成本统计。

## 目录结构

```text
personal-knowledge-radar/
  apps/
    api/
      app/
        api/routes/          FastAPI 路由
        agents/              Agent 实现
        collectors/          GitHub、RSS、网页采集器
        core/                配置、日志、安全、URL 防护
        db/                  SQLAlchemy base/session/types
        llm/                 LLM 和 embedding provider 抽象
        models/              SQLAlchemy 模型
        repositories/        数据访问层
        schemas/             Pydantic schemas
        services/            业务服务层
        tasks/               Celery app、beat 配置和核心业务任务入口
        tests/               后端测试
      alembic/               数据库迁移
      pyproject.toml
    web/                     Next.js 多页面工作台和后端 API 联调
  docs/
    DEVELOPMENT.md
    HANDOFF.md
  docker-compose.yml
  .env.example
  README.md
```

## 本地运行

Docker Compose：

```bash
cd personal-knowledge-radar
cp .env.example .env
docker compose up --build
```

执行迁移：

```bash
docker compose exec api alembic upgrade head
```

生产模式 Docker Compose：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

后端本地开发：

```bash
cd personal-knowledge-radar/apps/api
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
pytest
ruff check app
```

PowerShell 激活虚拟环境：

```powershell
.venv\Scripts\Activate.ps1
```

## 环境变量

见 `.env.example`。

重要变量：

- `APP_SECRET_KEY`：JWT 签名密钥，生产环境必须替换。
- `DATABASE_URL`：PostgreSQL 连接。
- `REDIS_URL`：Redis/Celery 连接。
- `LLM_PROVIDER`：`mock`、`openai_compatible`、`deepseek` 或 `qwen`。
- `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`、`EMBEDDING_MODEL`：真实模型配置。
- SMTP 变量：用于邮件推送真实发送。

测试环境在 `app/tests/conftest.py` 中强制使用 SQLite 和 mock LLM provider。

## 已有 API

健康检查：

- `GET /health`

认证：

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

偏好：

- `GET /api/preferences`
- `PUT /api/preferences`

内容提交：

- `POST /api/ingestions`：创建 pending job，并投递 Celery `process_ingestion_job`。
- `GET /api/ingestions`：查看当前用户任务列表。
- `GET /api/ingestions/{id}`：轮询任务状态。
- `POST /api/ingestions/{id}/replay`：重放当前用户自己的 failed 采集任务。

文档：

- `GET /api/documents`
- `POST /api/documents/from-content`
- `GET /api/documents/{id}`
- `DELETE /api/documents/{id}`

搜索和问答：

- `POST /api/search`
- `POST /api/chat`

推荐：

- `GET /api/recommendations`
- `POST /api/recommendations/generate`
- `POST /api/recommendations/{id}/ignore`
- `POST /api/recommendations/{id}/dislike`
- `POST /api/recommendations/{id}/save`

外部发现：

- `POST /api/discovery/github-trending`
- `POST /api/discovery/rss`

## 前端状态

当前 `apps/web` 已实现多页面工作台并接入后端：

- 创意登录界面：玻璃拟态卡片、雷达扫描动效、注册/登录表单，已接后端认证。
- 个人界面：仪表盘、文档页、推荐箱、搜索问答页、偏好设置页和快速采集。
- 已使用 Tailwind CSS v4 的 `@tailwindcss/postcss` 配置。

尚未完成：更细的加载/错误状态、完整业务细节页、前端自动化测试、生产级体验打磨。

推送：

- `POST /api/push/daily`
- `GET /api/push/logs`

## Celery 任务

当前已注册核心任务入口和定时调度：

- `process_ingestion_job`：处理已有 ingestion job；公开提交接口已投递这个任务。
- `fetch_daily_sources`：抓取 GitHub Trending 并生成当前用户推荐。
- `generate_user_recommendations`：基于输入内容创建并处理 ingestion。
- `embed_document_chunks`：为已有文档 chunks 重新生成 embedding。
- `cleanup_failed_jobs`：将超时的 running/retrying job 标记为 failed。

已补 Celery Beat 定时调度、任务自动重试策略、每日推荐推送任务、需要登录访问的 `/api/tasks/health`、`/api/tasks/schedule` 基础监控接口，以及单个 failed ingestion job 重放接口。后续还需要更完整的告警、批量重放和生产运维面板。

## 核心流程

### 手动提交内容

1. 用户调用 `POST /api/ingestions` 提交 URL 或文本。
2. 系统创建 pending ingestion job，并投递 Celery `process_ingestion_job`。
3. API 返回 `202 Accepted`、job 和 `task_id`，前端通过列表或详情接口轮询状态。
4. worker 将 job 标记 running。
5. 文本直接使用；URL 先校验安全性再抓取。
6. 创建或复用全局 content。
7. RouterAgent 选择路由和分类。
8. summary Agent 调用 `ChatModel` 生成结构化摘要；模型输出异常时降级为基础摘要。
9. 记录 agent run。
10. 更新 job 为 success 或 failed。

### 保存为知识库文档

1. 用户调用 `POST /api/documents/from-content`。
2. 从全局 `contents` 加载内容。
3. 为当前用户创建私有 document。
4. 同一用户重复保存同一 content 时复用已有 document。
5. 文本切片。
6. 生成 embedding。
7. 写入 `document_chunks`。

### 搜索和问答

1. 用户发送搜索词或问题。
2. 系统生成 query embedding。
3. 只检索当前用户自己的 chunks。
4. PostgreSQL 使用 pgvector 数据库侧 cosine distance 排序；SQLite 测试环境回退到 Python 侧余弦相似度排序。
5. chat 把检索片段传给 `ChatModel` 生成答案，并返回 citations。

### 推荐箱

1. 内容可以通过手动生成或 discovery 生成推荐。
2. 推荐初始状态为 `pending`。
3. 用户可以 ignore、dislike 或 save。
4. save 会创建当前用户私有 document。

### 外部发现

1. GitHub Trending 或 RSS 被采集。
2. 采集项写入或复用全局 content。
3. 为当前用户生成推荐。
4. 不会自动创建 document。

### 推送流程

1. 系统读取用户偏好和 pending 推荐。
2. 根据 `push_channel` 选择站内、邮件或钉钉。
3. 站内渠道只写 `push_logs`。
4. 邮件和钉钉需要 SMTP 或 webhook 配置，缺失时记录 skipped，不会误发。
5. `push_channel=disabled` 会跳过推送并记录日志。
6. 同一用户同一渠道当天已有 successful sent 时，后续触发会被频控跳过。
7. Celery Beat 会批量为活跃用户触发每日推荐推送。

## 安全规则

- 所有私有数据必须按 `user_id` 过滤。
- 不允许信任前端传入的 `user_id`。
- 不允许硬编码密钥。
- 不允许在日志中输出密码、token 或 API Key。
- URL 抓取必须使用 SSRF 防护，重定向后的最终 URL 也必须再次校验。
- 推荐保存和文档入库必须保持幂等。

## 集成验证

新增 `scripts/smoke_docker.ps1` 用于本地 Docker Compose 最小链路验证：

- 启动 PostgreSQL、Redis、API、worker、beat。
- 执行 Alembic migration。
- 检查 API `/health`、任务 schedule 和 worker health。
- 注册/登录 smoke 用户。
- 提交异步 ingestion job，并轮询到 success。

只验证脚本语法：

```powershell
.\scripts\smoke_docker.ps1 -ValidateOnly
```

完整 smoke：

```powershell
.\scripts\smoke_docker.ps1
```

## 测试

测试文件：

- `test_auth_preferences.py`
- `test_domain_foundation.py`
- `test_llm_providers.py`
- `test_ingestions.py`
- `test_documents_api.py`
- `test_search_chat.py`
- `test_recommendations.py`
- `test_discovery.py`
- `test_tasks.py`

运行：

```bash
pytest
ruff check app
```

最近结果：后端全量 `pytest` 为 59 passed；`ruff check app` passed；前端 `npm run build` passed；`npm install --package-lock-only` completed，但 npm audit 仍有 2 个 moderate 漏洞需后续治理。

## 已知风险

- PostgreSQL 已使用 pgvector 数据库侧排序，但仍缺少真实数据量下的召回评估、参数调优和 rerank。
- Celery 核心任务入口、公开 ingestion 异步投递、Beat 定时调度和基础重试策略已完成，但生产级告警和人工重放还没完成。
- GitHub Trending 解析依赖 GitHub HTML 结构，页面变化可能导致失效。
- RSS parser 是基础实现，不能覆盖所有 feed 边界情况。
- 前端已有多页面工作台，API client 已补超时、AbortController 和 401 登录过期处理；React Query、全局 toast/loading/error boundary 和自动化测试仍偏弱。
- 真实 LLM provider 接口已实现，但测试主要覆盖 mock 和 provider 解析逻辑；RAG 已补模型失败降级、上下文截断和 prompt 注入防护提示。

## 二期第一批交付结论

二期第一批可以视为完成。本轮交付集中在一期 MVP 的稳定性和交付质量：

- 安全：task 接口鉴权、重定向后 SSRF 校验。
- 任务：failed ingestion job 单个重放。
- 推送：禁用通道、当日成功推送频控。
- 前端：API timeout、AbortController、统一 ApiError、401 登录过期处理。
- 生产：锁定前端依赖，新增 `docker-compose.prod.yml`。
- 推荐：模型辅助推荐决策，保留规则 fallback。

三期建议优先做 CI/CD、真实 provider 质量评估、React Query/toast/error boundary、审计日志、管理员权限模型和投递告警，再考虑浏览器插件、视频字幕和管理后台。

## 当前风险修补队列

根据用户提供的外部分析，以下是当前最重要的风险和修补路线。接手者应优先处理这些问题，而不是继续横向增加新模块。

### 需要承认的现状

- 当前项目已经具备多用户、知识库、推荐、搜索、推送、前端工作台等骨架和部分真实能力。
- 但仍不是完整生产产品，代码中同时存在真实能力、mock 能力、占位模型和生产待办。
- 文档描述必须避免过度乐观，尤其是 summary、recommendation、真实部署验证这些部分；Celery ingestion 异步化和 ChatModel RAG 基础接入已完成，但仍缺生产告警、人工重放和真实 provider 质量评估。

### 已确认仍需修补

- `RecommenderAgent` 已接入模型辅助决策并保留规则 fallback；仍缺真实 provider 评估、用户反馈学习和个性化权重。
- Docker Compose smoke 脚本已补 task 认证、pgvector extension 断言和失败日志收集；仍缺 CI 接入、真实 provider 可选验证和完整清理策略。
- `/api/tasks/health` 和 `/api/tasks/schedule` 已要求登录；后续还需管理员权限模型。
- URL 抓取已对重定向后的最终 URL 再次做 SSRF 校验。
- 前端 token 存 localStorage，logout 只是本地清除 token；后续需要 token 黑名单或服务端会话撤销策略。
- 前端 API client 已补 timeout、AbortController 和统一 401；仍缺 React Query 实际接入、toast/loading/error boundary 和页面级 skeleton。
- 前端依赖已锁定，已新增生产 compose override；仍需治理 npm audit 漏洞、多阶段镜像、CI 构建和部署环境差异。
- ORM 与 migration 类型口径需在真实 PostgreSQL 上复查。

### 本轮已推进

- `/api/ingestions` 主接口已从同步处理改为创建 pending job 并投递 Celery，返回 `202 Accepted` 和 `task_id`。
- 前端快速采集已改为异步提交提示，提交后刷新任务列表，不再假设立即拿到 content。
- `SearchService.chat()` 已从模板拼接改为检索后调用 `ChatModel` 生成答案，并继续返回 citations；已补模型失败降级、上下文截断和 prompt 注入防护提示。
- `GeneralAgent`、`GitHubAgent`、`LifestyleAgent` 已从规则/固定摘要改为调用 `ChatModel` 生成结构化 JSON，并保留 fallback。
- 已更新受影响后端测试，覆盖异步提交、worker 处理、下游文档/推荐/搜索链路、RAG prompt 和 summary fallback。
- 已新增 Docker Compose smoke 脚本，覆盖 Alembic、API、worker、beat、pgvector extension、带认证 task 监控接口和异步 ingestion 最小链路。
- 已完成二期安全收口第一批：任务监控接口要求登录，URL 重定向后的最终地址再次经过 SSRF 校验。
- 已新增单个 failed ingestion job 重放接口，覆盖成功、冲突和用户隔离测试。
- 已完成推送控制第一批：支持禁用推送通道和基于 push log 的当日成功推送频控。
- 已完成前端 API client 工程化第一批：默认超时、AbortController、统一 ApiError 和 401 登录过期事件。
- 已完成生产可复现第一批：前端依赖锁定，新增 `docker-compose.prod.yml`，web 生产模式使用 build + start。
- 已完成推荐模型化第一批：`RecommenderAgent` 调用 `ChatModel` 输出结构化推荐决策，并保留规则 fallback。
- 已完成 RAG 生产质量增强第一批：模型失败降级、上下文截断和 prompt 注入防护提示。
- 已完成 Docker smoke 增强第一批：task 认证适配、pgvector extension 断言和失败日志收集。

### 已修补或部分过期

- 搜索中文乱码已修复。
- pgvector 数据库侧排序已实现，并保留 SQLite 回退。
- 推送基础能力、禁用通道和当日成功推送频控已实现；生产模板、带签名退订链接、可配置频控和投递告警仍未完成。
- 前端已不是单一占位页，已有多页面工作台，但工程体验还需打磨。

### 建议下一步顺序

1. 修正文档口径：明确标注 mock / 规则 / 占位 / 真实能力。
2. 增强 RAG 和总结生产质量：真实 provider 验证、引用编号稳定性评估、召回评估、rerank 和人工反馈调优。
3. 推荐质量增强：真实 provider 评估、用户反馈学习、个性化权重和去重排序策略。
4. 增强 Docker Compose 集成验证：接入 CI、真实 provider 可选验证、完整清理策略和失败产物归档。
5. 安全加固增强：管理员权限模型、token 黑名单或服务端会话撤销、前端 401 统一处理和审计日志落库。
6. 前端工程化增强：React Query、全局 toast/loading/error boundary、页面级 skeleton、自动化测试和依赖版本锁定。

## 建议下一步

1. 完成更完整的任务监控告警、批量失败任务重放和生产运维面板。
2. 增强推送模板、带签名退订链接、可配置频控、投递告警和操作链接。
3. 前端工程化：React Query、全局 toast/loading/error boundary、页面级 skeleton、自动化测试和依赖版本锁定。
4. 做 pgvector 召回评估、参数调优和 rerank。
5. 增加 Docker Compose 端到端验证。

## 文档维护规则

以后每次任务结束前，都要检查是否需要更新：

- `README.md`
- `docs/DEVELOPMENT.md`
- `docs/HANDOFF.md`

不要只改代码不改文档。
