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

## v0.1.1 — UI 重设计（2026-05-04）

### 做什么
- 整体 UI 重设计：Apple 风格磨砂玻璃侧边栏 + 头部
- SVG Logo：亮色/暗色两套，严格黑白灰三色，字母 C 居中
- Lucide 图标：替代 emoji 图标，全界面统一
- favicon 添加到 index.html
- i18n 标题「蠢人书签」中英文支持
- 中/英文切换控件
- 后端 API 模块改进

### 为什么
- 用户要求整体视觉升级，黑白灰配色保持克制
- Logo 简化，放弃汉字改用字母 C
- 日夜切换需要对应的两套 SVG

### 怎么做
- 修改 33 个文件，+6925/-244
- 前端：AdminLayout, AuthLayout, Login, Dashboard, Bookmarks, Audit, Model, main.css, tailwind.config.js
- 后端：auth, bookmarks, recommend, config, database, security 等模块改进

---

## v0.1.0 — MVP 发布（2026-04-28）

### 做什么
- 完成全 8 个 Phase 的开发
- 后端：FastAPI + SQLAlchemy + Alembic + JWT 认证 + 结构化日志
- 数据摄入：网页爬取 + Claude API 补全 + 书签入库 + 审计日志
- 推荐系统：ChromaDB + sentence-transformers 向量搜索 + 模型版本追踪
- 前端：Vue 3 + Vite + TypeScript + Tailwind CSS + i18n 中/英
- 三套环境配置 + Docker Compose 一键部署 + README 文档
- 后端测试 + 前端 Vitest 配置

### 为什么
- MVP 版本需要覆盖完整流程：摄入 → 补全 → 推荐 → 管理
- 用户要求轻量部署，选用 SQLite + ChromaDB
- 推荐需要语义理解，选用 sentence-transformers 向量搜索

### 怎么做
- 后端 4 个 API 模块：auth / bookmarks / recommend / admin
- 前端 5 个页面：Login / Dashboard / Bookmarks / Audit / Model
- 数据库 4 张表：br_users / br_bookmarks / br_audit_logs / br_model_versions
- Docker Compose 编排后端 + 前端，Nginx 代理 API

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
