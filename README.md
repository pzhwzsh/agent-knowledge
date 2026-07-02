# 个人信息雷达与知识库 Agent 平台

个人信息雷达是一个多用户 AI 知识库平台。你可以把文章、网页、GitHub 仓库、RSS 内容和纯文本保存进系统，让系统帮你抓取、分类、总结、推荐、入库，并在以后通过搜索或问答找回来。

它不是普通收藏夹，而是一个可部署的 Agent 知识管理平台，目标是成为你的个人第二大脑。

## 当前已经能做什么

当前后端 MVP 已经支持：

- 用户注册、登录和服务端登出撤销新 token。
- 每个用户拥有自己的私有知识库。
- 配置兴趣关键词、不感兴趣关键词、启用分类和推送相关字段。
- 手动提交 URL 或纯文本。
- 抓取网页正文并提取可读内容。
- URL 安全检查，阻止 localhost、内网地址和保留地址；重定向后的最终 URL 也会再次校验，降低 SSRF 风险。
- 全局内容表 `contents` 去重。
- RouterAgent 路由和基于 `ChatModel` 的结构化摘要 Agent；模型返回异常时会降级为基础摘要。
- 将内容保存到当前用户的私有知识库。
- 文档切片和 embedding 生成。
- 在当前用户自己的文档中做语义搜索，PostgreSQL 使用 pgvector 数据库侧排序，SQLite 测试环境自动回退到 Python 余弦相似度。
- 基于自己的知识库进行 RAG 问答：先检索当前用户私有文档片段，再调用 `ChatModel` 生成答案并返回引用；已加入上下文截断、prompt 注入防护提示和模型失败降级。
- 推荐箱：模型辅助推荐决策，保留规则 fallback；会根据用户保存/忽略/不喜欢反馈调整后续推荐分；推荐内容不会自动入库。
- 推荐操作：忽略、不感兴趣、保存。
- GitHub Trending 和 RSS 发现，发现结果进入推荐箱，不直接进入知识库。
- Celery 后台任务：核心任务入口、Beat 定时调度、任务重试策略、活跃用户每日来源抓取、每日推荐推送、超时任务清理、过期撤销 token 清理和管理员保护的基础监控接口。
- 推送能力：站内推送日志、邮件推送、钉钉推送、推送日志查询、手动触发每日推荐推送、禁用推送通道和每日成功推送频控。
- 前端已接入后端：支持注册、登录、token 保存、服务端登出撤销、登录过期统一处理、API 超时控制、React Query 基础数据缓存、文档页/偏好页/搜索问答页 React Query 数据管理、统一 query 错误 toast、全局 toast 提示、全局错误页、页面级 skeleton、仪表盘、文档、推荐箱、搜索问答、偏好设置、快速采集和反馈维修台；管理员可进入反馈处理后台查看全部反馈并更新处理状态，也可以进入审计日志页面查看敏感操作记录。

## 二期第一批状态

二期第一批已完成：安全收口、任务重放、推送控制、前端 API client 工程化、生产 compose、模型辅助推荐、使用反馈闭环和反馈处理后台第一版、审计日志查询第一版和服务端登出撤销第一版和撤销 token 清理任务第一版和全局 toast 第一批和全局错误页第一批和页面级 skeleton 第一批、Search React Query 迁移第一批和统一 Query UX 第一批。当前项目仍不是完整商业化生产版本，三期会继续补 CI/CD、管理后台、审计日志、React Query/toast/error boundary、浏览器插件、视频字幕、Rerank 和多模型路由等能力。

## 当前还没有完成什么

以下功能还没有完成或还不能按生产能力使用：

- 前端更细的交互状态、更多业务细节页面和生产级体验打磨。
- 更完整的任务监控告警、失败任务人工重放和生产运维面板。
- 每日定时推荐。
- 邮件真实发送需要配置 SMTP。
- 钉钉真实发送需要配置 webhook。
- 视频字幕解析。
- PDF 完整解析。
- 浏览器插件。
- 完整管理后台仍未完成；当前仅有反馈处理后台第一版、审计日志查询第一版和服务端登出撤销第一版和撤销 token 清理任务第一版和全局 toast 第一批和全局错误页第一批和页面级 skeleton 第一批、Search React Query 迁移第一批和统一 Query UX 第一批。
- 知识库导出。
- 更细的 pgvector 参数调优、召回评估和重排策略。

## 适合谁使用

这个项目适合：

- 经常收藏链接但后来找不到的人。
- 想让 AI 总结文章和 GitHub 项目的人。
- 想搭建自己的私有可搜索知识库的人。
- 想对自己的资料做带引用问答的人。
- 想学习 Agent 平台后端架构的人。

## 快速启动

进入项目目录：

```bash
cd personal-knowledge-radar
```

复制环境变量文件：

```bash
cp .env.example .env
```

启动所有服务：

```bash
docker compose up --build
```

首次启动后执行数据库迁移：

```bash
docker compose exec api alembic upgrade head
```

生产模式启动（API 不开启 reload，web 使用 build + start）：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```


## 集成验证

本地 Docker 环境可运行最小 smoke test，用来验证 PostgreSQL/pgvector、Redis、API、Celery worker、Celery Beat、Alembic、带认证的 task 监控接口和异步采集链路；失败时会收集核心服务日志：

```powershell
.\scripts\smoke_docker.ps1
```

只检查脚本是否能被 PowerShell 解析，不启动 Docker：

```powershell
.\scripts\smoke_docker.ps1 -ValidateOnly
```

## 主要 API

认证：

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

用户偏好：

- `GET /api/preferences`
- `PUT /api/preferences`

内容提交：

内容提交采用异步任务：前端提交后先看到 pending job，后台 worker 负责抓取、解析、路由、摘要和状态更新。

- `POST /api/ingestions`：提交 URL 或文本，返回 `202 Accepted`、pending job 和 Celery `task_id`。
- `GET /api/ingestions`：查看当前用户的采集任务列表。
- `GET /api/ingestions/{id}`：轮询单个采集任务状态。
- `POST /api/ingestions/{id}/replay`：重放当前用户自己的 failed 采集任务。

知识库文档：

- `GET /api/documents`
- `POST /api/documents/from-content`
- `GET /api/documents/{id}`
- `DELETE /api/documents/{id}`

搜索和问答：

- `POST /api/search`
- `POST /api/chat`：基于当前用户知识库片段调用 `ChatModel` 生成带引用答案。

推荐箱：

- `GET /api/recommendations`
- `POST /api/recommendations/generate`
- `POST /api/recommendations/{id}/ignore`
- `POST /api/recommendations/{id}/dislike`
- `POST /api/recommendations/{id}/save`

反馈与管理员处理：

- `POST /api/feedback`：提交当前用户自己的使用反馈。
- `GET /api/feedback`：查看当前用户自己的反馈记录。
- `GET /api/feedback/admin/all`：管理员查看全部用户反馈，可按 status 筛选。
- `PATCH /api/feedback/admin/{id}`：管理员更新反馈处理状态，并写入审计日志。
- `GET /api/audit/logs`：管理员查询审计日志，可按 user_id、action、resource_type 筛选。

外部发现：

- `POST /api/discovery/github-trending`
- `POST /api/discovery/rss`

## LLM Provider 配置

开发和测试时可以使用 mock provider：

```env
LLM_PROVIDER=mock
```

如果要接真实模型，可以使用 OpenAI Compatible API、DeepSeek 或 Qwen：

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://example.com/v1
LLM_API_KEY=your-key
LLM_MODEL=your-chat-model
EMBEDDING_MODEL=your-embedding-model
```

不要把真实 API Key 提交到代码仓库。

## 开发文档

请查看：

- `docs/DEVELOPMENT.md`
- `docs/HANDOFF.md`

## 文档维护规则

以后每次改功能、接口、数据库、后台任务、部署方式或测试，都要同步更新文档：

- 用户能感知的变化，更新 `README.md`。
- 开发阶段、API、模型、任务或测试变化，更新 `docs/DEVELOPMENT.md`。
- 交接说明、风险、运行方式和下一步变化，更新 `docs/HANDOFF.md`。
