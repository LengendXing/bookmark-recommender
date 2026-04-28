# MAINTAIN.md — 版本迭代记录

**业务前缀**: `br_`（数据库表、Redis Key、缓存键等统一使用此前缀）

## 版本规范

格式：`v{大}.{中}.{小}`

| 版本类型 | 触发条件 | 操作 |
|---|---|---|
| 大版本 | 用户通知大更新 | main 打 tag，记录重大变更 |
| 中版本 | 用户通知发布 | dev 合并到 main，打 tag |
| 小版本 | 每次提交自动 | 小版本 +1，自动 commit+push |

---

## v0.0.0 — 项目初始化（2026-04-28）

### 做什么
- 创建技术方案文档与开发计划
- 确定技术栈：Python 3.12 + FastAPI + Vue 3 + Tailwind CSS + shadcn/ui
- 确定数据存储：SQLite（业务数据）+ ChromaDB（向量数据）
- 确定 AI 引擎：Claude API（网页爬取 + 字段补全 + 标签生成）
- 确定推荐模型：sentence-transformers embedding + ChromaDB 相似度搜索

### 为什么
- 项目从零开始，需要明确架构方向
- 用户要求轻量部署，前期不用 PostgreSQL，选用 SQLite
- 推荐需要语义理解能力，TF-IDF 不够，选用 ChromaDB 向量搜索

### 怎么做
- 编写完整技术方案文档
- 按 18 条规范要求设计架构（版本管理、安全、i18n、Docker、分支策略等）
- 制定分阶段开发计划（PLAN.md）
