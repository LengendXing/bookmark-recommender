# 开源项目「一键分析 + 智能推荐」技术方案

## 版本

v0.1.0 / 2026-05-06

## 需求概述

1. **一键分析**：通过 AI 挖掘已 star 项目的详细信息（topics/tags、详细描述、许可证、主页等），补齐 `br_starred_repos` 表扩展字段。
2. **智能推荐**：基于用户关注的标签/领域，AI 自动从 GitHub 搜索同类型优质项目，存入新建的推荐项目表。
3. **推荐交付**：定时 SSE 主动推送 + API 拉取两种方式。
4. **UI 改造**：点击项目名称弹出右侧抽屉展示详情，不再跳转 GitHub。

---

## 一、数据库设计

### 1.1 扩展 `br_starred_repos` 表（新增字段）

| 字段 | 类型 | 说明 |
|------|------|------|
| `topics` | `Text` | JSON 数组，GitHub 项目标签，如 `["machine-learning","nlp"]` |
| `homepage` | `Text` | 项目主页 URL |
| `license` | `String(64)` | 开源许可证，如 `MIT`、`Apache-2.0` |
| `open_issues` | `Integer` | 开放 issue 数量 |
| `watchers` | `Integer` | Watcher 数量 |
| `size_kb` | `Integer` | 仓库大小（KB） |
| `language_color` | `String(16)` | 语言颜色 hex |
| `default_branch` | `String(64)` | 默认分支 |
| `archived` | `Boolean` | 是否已归档 |
| `readme_text` | `Text` | README 前 3000 字符，AI 分析用 |
| `ai_tags` | `Text` | AI 归纳的标签 JSON 数组 |
| `ai_summary` | `Text` | AI 生成的项目一句话摘要 |
| `ai_category` | `String(64)` | AI 分类（如 前端框架/ML/AI 工具/DevOps） |
| `ai_analyzed_at` | `String` | AI 分析完成时间 |
| `analyze_error` | `Text` | 分析失败时的错误信息 |

### 1.2 新建 `br_recommended_repos` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `Integer PK` | 自增主键 |
| `user_id` | `Integer` | 所属用户 |
| `repo_full_name` | `String(256)` | `owner/name` |
| `repo_name` | `String(128)` | 仓库名 |
| `owner` | `String(128)` | 所有者 |
| `html_url` | `Text` | GitHub 页面 URL |
| `clone_url` | `Text` | 克隆地址 |
| `description` | `Text` | GitHub 原始描述 |
| `ai_summary` | `Text` | AI 生成的中文摘要 |
| `topics` | `Text` | JSON 数组，GitHub 官方 topics |
| `ai_tags` | `Text` | AI 归纳的标签 |
| `language` | `String(64)` | 主要语言 |
| `language_color` | `String(16)` | 语言颜色 |
| `stars` | `Integer` | Star 数 |
| `forks` | `Integer` | Fork 数 |
| `open_issues` | `Integer` | 开放 issue 数 |
| `watchers` | `Integer` | Watcher 数 |
| `license` | `String(64)` | 许可证 |
| `homepage` | `Text` | 项目主页 |
| `default_branch` | `String(64)` | 默认分支 |
| `size_kb` | `Integer` | 仓库大小 |
| `archived` | `Boolean` | 是否归档 |
| `score` | `Float` | 推荐评分（AI 计算，0-100） |
| `recommend_reason` | `Text` | 推荐理由（为什么匹配你的兴趣） |
| `match_tags` | `Text` | 匹配了哪些用户关注的标签 |
| `source_tag` | `String(128)` | 通过哪个标签搜索到的 |
| `is_read` | `Boolean` | 用户是否已读（默认 False） |
| `is_starred` | `Boolean` | 用户是否已 star（默认 False） |
| `recommended_at` | `String` | 推荐生成时间 |
| `created_at` | `DateTime` | 记录创建时间 |
| `updated_at` | `DateTime` | 记录更新时间 |

索引：
- `(user_id, repo_full_name)` 联合唯一索引，防止重复推荐
- `(user_id, is_read)` 用于查询未读推荐
- `(user_id, recommended_at)` 用于按时间排序

---

## 二、后端 API 设计

### 2.1 新增端点

#### `POST /api/github/repos/analyze-all`
启动后台异步分析所有已 star 项目（补全扩展字段）。

流程：
1. 遍历用户所有 `br_starred_repos` 中 `topics IS NULL` 或 `ai_analyzed_at IS NULL` 的记录
2. 对每条调用 GitHub API `GET /repos/{full_name}` 获取 topics、license、homepage 等
3. 同时获取 README 文件内容（GitHub API `GET /repos/{full_name}/readme`）
4. 调用 AI 对 README + description 做归纳，生成 `ai_tags`、`ai_summary`、`ai_category`
5. 写入数据库，更新进度（类似 bookmark 的 `_analysis_progress`）

#### `GET /api/github/repos/analyze-progress`
返回分析进度 `{total, completed, running, error}`。

#### `GET /api/github/repos/{repo_id}`
返回单个项目的完整详细信息（供前端 Drawer 展示）。

#### `POST /api/github/recommendations/generate`
触发一次推荐生成（手动触发）。

流程：
1. 从 `br_starred_repos` 中汇总用户的所有 tags/topics/ai_tags
2. 去重、排序（按出现频率），取 TopK 标签（K=3，怕 API 频率限制）
3. 对每个标签调用 GitHub Search API `GET /search/repositories?q=topic:{tag}&sort=stars&per_page=10`
4. 过滤掉用户已 star 的项目（通过 `repo_full_name` 去重）
5. 对候选项目调用 GitHub API 获取详细信息
6. 调用 AI 打分 + 生成推荐理由
7. 存入 `br_recommended_repos`

#### `GET /api/github/recommendations`
拉取推荐列表：
- `GET /api/github/recommendations` — 全部推荐（分页）
- `GET /api/github/recommendations?unread=true` — 只看未读

#### `PUT /api/github/recommendations/{id}/read`
标记单条推荐为已读。

#### `GET /api/github/recommendations/sse`
SSE 端点，每 30 秒推送一条未读推荐或心跳。前端可以连接此端点实时接收推荐。

---

## 三、后端 Service 设计

### 3.1 修改 `app/services/github_service.py`

新增函数：
- `get_repo_detail(token, repo_full_name)` — 获取仓库详细信息（topics、license、homepage 等）
- `get_repo_readme(token, repo_full_name)` — 获取 README 内容
- `search_repos_by_topic(token, topic, per_page)` — 按标签搜索仓库

### 3.2 新增 `app/services/recommendation_service.py`

核心推荐逻辑：
- `extract_user_tags(user_id)` — 汇总用户关注的标签
- `discover_candidates(user_id, top_tags)` — GitHub 搜索候选项目
- `filter_and_score(candidates, user_repos)` — AI 打分过滤
- `store_recommendations(user_id, scored_candidates)` — 存入推荐表

### 3.3 修改 `app/services/ai_service.py`

新增函数：
- `analyze_repo(repo_data)` — 对单个仓库做 AI 分析，返回 tags、summary、category

### 3.4 定时任务（`app/main.py`）

在 APScheduler 中添加每日推荐生成任务（每天凌晨 3 点执行一次）：
```python
scheduler.add_job(
    generate_daily_recommendations,
    trigger=CronTrigger(hour=3, minute=0),
    ...
)
```

---

## 四、前端设计

### 4.1 新增 `RepoDrawer.vue` 组件

类似现有的 `BookmarkDrawer.vue`，从右侧滑入展示项目详情：

展示内容：
- **基本信息**：名称、Owner、Full Name、语言（带颜色点）、License
- **数据**：Stars、Forks、Watchers、Open Issues、Size
- **链接**：GitHub 页面、Homepage（可点击跳转）
- **标签（Topics）**：彩色标签组
- **AI 分析**：AI 摘要、AI 标签、AI 分类
- **README 预览**：前 500 字符

### 4.2 修改 `GitHubProjects.vue`

- 点击项目名称改为打开 `RepoDrawer` 而非 `window.open()`
- 「一键分析」按钮绑定 `analyzeRepos()` 函数，显示进度条
- 新增「推荐」Tab/按钮，展示推荐项目列表

### 4.3 新增 `RecommendationList.vue`（或内嵌在 GitHubProjects.vue 中）

- 推荐列表表格
- 每行显示：项目名、推荐理由、匹配标签、评分、Star 数
- 未读推荐高亮显示
- 点击项目名打开 RepoDrawer

### 4.4 修改 `src/api/index.ts`

新增 API 调用：
```typescript
export const github = {
  // ... existing ...
  analyzeRepos: () => request.post('/github/repos/analyze-all'),
  analyzeProgress: () => request.get('/github/repos/analyze-progress'),
  getRepoDetail: (id: number) => request.get(`/github/repos/${id}`),
  generateRecommendations: () => request.post('/github/recommendations/generate'),
  listRecommendations: (params?: any) => request.get('/github/recommendations', { params }),
  markRecommendationRead: (id: number) => request.put(`/github/recommendations/${id}/read`),
}
```

---

## 五、数据流

```
用户 Star 的项目（br_starred_repos）
        │
        ▼
  ┌─ 一键分析 ─────────────────────┐
  │  1. GitHub API 获取 topics,     │
  │     readme, license 等          │
  │  2. AI 归纳 ai_tags/summary/    │
  │     category                    │
  │  3. 写入 br_starred_repos       │
  └─────────────────────────────────┘
        │
        ▼
  ┌─ 智能推荐生成 ──────────────────┐
  │  1. 提取用户关注标签 TopK        │
  │  2. GitHub Search API 搜候选     │
  │  3. 过滤已 star 项目            │
  │  4. AI 打分 + 推荐理由          │
  │  5. 写入 br_recommended_repos   │
  └─────────────────────────────────┘
        │
        ├──► API GET /recommendations  （拉取）
        └──► SSE /recommendations/sse  （推送）
```

---

## 六、GitHub API 频率限制

- 认证用户 5000 req/hour
- Search API 30 req/min，10 req/min 不带认证
- 应对策略：
  - 标签搜索 TopK 收敛为 3-5 个
  - 分析时串行 + sleep 间隔
  - 每日定时只跑一次
  - 手动触发入口可选

---

## 七、文件变更清单

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `backend/app/models/starred_repo.py` | 新增 14 个扩展字段 |
| 新增 | `backend/app/models/recommended_repo.py` | 推荐项目表模型 |
| 修改 | `backend/app/models/__init__.py` | 导出新模型 |
| 修改 | `backend/app/schemas/github.py` | 新增 schema |
| 修改 | `backend/app/services/github_service.py` | 新增 3 个函数 |
| 修改 | `backend/app/services/ai_service.py` | 新增 `analyze_repo()` |
| 新增 | `backend/app/services/recommendation_service.py` | 推荐核心逻辑 |
| 修改 | `backend/app/api/github.py` | 新增 analyze、detail、recommendation 端点 |
| 修改 | `backend/app/main.py` | 注册新路由 + 定时任务 |
| 新增 | `backend/migrations/002_add_repo_fields.sql` | 扩展字段迁移 |
| 新增 | `backend/migrations/003_create_recommended_repos.sql` | 推荐表迁移 |
| 新增 | `frontend/src/components/RepoDrawer.vue` | 项目详情抽屉 |
| 修改 | `frontend/src/pages/GitHubProjects.vue` | 抽屉集成 + 推荐列表 |
| 修改 | `frontend/src/api/index.ts` | 新增 API 调用 |

---

## 八、里程碑计划

- [ ] M1 — 数据库扩展 + 迁移（StarredRepo 扩展字段 + RecommendedRepo 表）
- [ ] M2 — GitHub API 扩展 + AI 分析（一键分析功能）
- [ ] M3 — 推荐引擎（标签提取 + GitHub 搜索 + AI 打分 + 存储）
- [ ] M4 — SSE 推送 + API 拉取（推荐交付）
- [ ] M5 — RepoDrawer 组件 + UI 改造
- [ ] M6 — 定时任务 + 联调测试
- [ ] M7 — lint / build / test + 代码提交
