# 个人信息雷达与知识库 Agent 平台

个人信息雷达是一个多用户 AI 知识库平台。你可以把文章、网页、GitHub 仓库、RSS 内容和纯文本保存进系统，让系统帮你抓取、分类、总结、推荐、入库，并在以后通过搜索或问答找回来。

它不是普通收藏夹，而是一个可部署的 Agent 知识管理平台，目标是成为你的个人第二大脑。

## 当前已经能做什么

当前后端 MVP 已经支持：

- 用户注册和登录。
- 每个用户拥有自己的私有知识库。
- 配置兴趣关键词、不感兴趣关键词、启用分类和推送相关字段。
- 手动提交 URL 或纯文本。
- 抓取网页正文并提取可读内容。
- URL 安全检查，阻止 localhost、内网地址和保留地址，降低 SSRF 风险。
- 全局内容表 `contents` 去重。
- RouterAgent 路由和 mock Agent 摘要。
- 将内容保存到当前用户的私有知识库。
- 文档切片和 embedding 生成。
- 在当前用户自己的文档中做语义搜索。
- 基于自己的知识库进行带引用问答。
- 推荐箱：推荐内容不会自动入库。
- 推荐操作：忽略、不感兴趣、保存。
- GitHub Trending 和 RSS 发现，发现结果进入推荐箱，不直接进入知识库。
- Celery 后台任务：核心任务入口、Beat 定时调度、任务重试策略、活跃用户每日来源抓取、超时任务清理和基础监控接口。
- 前端已接入后端：支持注册、登录、token 保存、退出登录、仪表盘、文档、推荐箱、搜索问答、偏好设置和快速采集。

## 当前还没有完成什么

以下功能还没有完成或还不能按生产能力使用：

- 前端更细的交互状态、更多业务细节页面和生产级体验打磨。
- 更完整的任务监控告警、失败任务人工重放和生产运维面板。
- 每日定时推荐。
- 邮件推送。
- 钉钉推送。
- 视频字幕解析。
- PDF 完整解析。
- 浏览器插件。
- 管理后台。
- 知识库导出。
- 生产级 pgvector 数据库侧向量排序。

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


## 主要 API

认证：

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

用户偏好：

- `GET /api/preferences`
- `PUT /api/preferences`

内容提交：

- `POST /api/ingestions`
- `GET /api/ingestions`
- `GET /api/ingestions/{id}`

知识库文档：

- `GET /api/documents`
- `POST /api/documents/from-content`
- `GET /api/documents/{id}`
- `DELETE /api/documents/{id}`

搜索和问答：

- `POST /api/search`
- `POST /api/chat`

推荐箱：

- `GET /api/recommendations`
- `POST /api/recommendations/generate`
- `POST /api/recommendations/{id}/ignore`
- `POST /api/recommendations/{id}/dislike`
- `POST /api/recommendations/{id}/save`

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
