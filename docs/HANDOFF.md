# 交接文档

本文档用于项目交接。以后任何会影响行为、运行方式、API、测试、风险或下一步计划的代码变更，都必须同步更新本文档和 `docs/DEVELOPMENT.md`。

## 当前状态

本项目是一个多用户 AI 知识库平台。当前后端已支持认证、偏好、内容提交、文档入库、搜索、带引用问答、推荐箱和 GitHub/RSS 发现；前端已接入后端认证、token 保存、仪表盘、文档、推荐箱、搜索问答、偏好设置和快速采集。

当前主要缺口：

- 更完整的任务监控告警、失败任务人工重放和生产运维面板。
- 更完整的推送模板、退订、频控和投递告警。
- 前端更细的交互状态、更多业务细节页面和生产级体验打磨。

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

- `POST /api/ingestions`
- `GET /api/ingestions`
- `GET /api/ingestions/{id}`

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

- `process_ingestion_job`：处理已有 ingestion job。
- `fetch_daily_sources`：抓取 GitHub Trending 并生成当前用户推荐。
- `generate_user_recommendations`：基于输入内容创建并处理 ingestion。
- `embed_document_chunks`：为已有文档 chunks 重新生成 embedding。
- `cleanup_failed_jobs`：将超时的 running/retrying job 标记为 failed。

已补 Celery Beat 定时调度、任务自动重试策略、每日推荐推送任务和 `/api/tasks/health`、`/api/tasks/schedule` 基础监控接口。后续还需要更完整的告警、失败任务人工重放和生产运维面板。

## 核心流程

### 手动提交内容

1. 用户调用 `POST /api/ingestions` 提交 URL 或文本。
2. 系统创建 ingestion job。
3. 文本直接使用；URL 先校验安全性再抓取。
4. 创建或复用全局 content。
5. RouterAgent 选择路由和分类。
6. mock Agent 生成摘要。
7. 记录 agent run。
8. 更新 job 状态。

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
4. 使用 Python 侧余弦相似度排序。
5. chat 返回答案和 citations。

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
5. Celery Beat 会批量为活跃用户触发每日推荐推送。

## 安全规则

- 所有私有数据必须按 `user_id` 过滤。
- 不允许信任前端传入的 `user_id`。
- 不允许硬编码密钥。
- 不允许在日志中输出密码、token 或 API Key。
- URL 抓取必须使用 SSRF 防护。
- 推荐保存和文档入库必须保持幂等。

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

最近结果：`pytest` 47 passed，`ruff check app` passed，前端 `npm run build` passed。

## 已知风险

- 搜索排序目前是 Python 侧实现，不是 PostgreSQL/pgvector 数据库侧排序。
- Celery 核心任务入口、Beat 定时调度和基础重试策略已完成，但生产级告警和人工重放还没完成。
- worker 容器存在，但任务覆盖不完整。
- GitHub Trending 解析依赖 GitHub HTML 结构，页面变化可能导致失效。
- RSS parser 是基础实现，不能覆盖所有 feed 边界情况。
- 前端只是占位。
- 真实 LLM provider 接口已实现，但测试主要覆盖 mock 和 provider 解析逻辑。

## 建议下一步

1. 完成更完整的任务监控告警、失败任务人工重放和生产运维面板。
2. 增强推送模板、退订、频控、投递告警和带签名的操作链接。
3. 实现前端页面：login、register、dashboard、ingest、recommendations、documents、search、settings。
4. 将搜索排序迁移到 PostgreSQL/pgvector。
5. 增加 Docker Compose 端到端验证。

## 文档维护规则

以后每次任务结束前，都要检查是否需要更新：

- `README.md`
- `docs/DEVELOPMENT.md`
- `docs/HANDOFF.md`

不要只改代码不改文档。
