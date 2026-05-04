# PLAN.md — 开发计划

**当前版本**: `v0.1.1`
**当前分支**: `dev`

---

## 已完成

- [x] 技术方案设计（架构、技术栈、数据存储选型）
- [x] MAINTAIN.md 创建，记录 v0.0.0 初始化
- [x] PLAN.md 创建，制定开发计划

## 已完成 ✅ — Phase 1：项目骨架

- [x] P1-1 初始化 Git 仓库，创建 dev 分支
- [x] P1-2 创建 `.gitignore`、`.env.example`
- [x] P1-3 初始化后端项目（uv + FastAPI + pyproject.toml）
- [x] P1-4 初始化前端项目（Vue 3 + Vite + TypeScript + Tailwind + shadcn/ui）
- [x] P1-5 创建 Dockerfile + docker-compose.yml
- [x] P1-6 创建目录结构（backend/app, frontend/src 等）

## 已完成 ✅ — Phase 2：后端基础设施

- [x] P2-1 配置管理（config.py），读取 .env，版本常量维护
- [x] P2-2 SQLite 连接层（aiosqlite + SQLAlchemy 异步引擎）
- [x] P2-3 Alembic 初始化，创建首条迁移（br_bookmarks, br_users, br_audit_logs, br_model_versions）
- [x] P2-4 统一响应格式 `{code, message, data}` + 错误码规范
- [x] P2-5 结构化日志中间件
- [x] P2-6 JWT 认证中间件（Token 签发/验证/吊销）
- [x] P2-7 输入校验层（pydantic model 验证）

## 已完成 ✅ — Phase 3：数据摄入接口

- [x] P3-1 网页爬取服务（httpx + BeautifulSoup）
- [x] P3-2 Claude API 补全服务（字段补全 + 标签生成）
- [x] P3-3 `POST /api/ingest` 接口（动态判断单条/列表）
- [x] P3-4 数据写入 SQLite（含审计日志记录）
- [x] P3-5 单元测试：ingest 解析逻辑、字段补全、数据写入

## 已完成 ✅ — Phase 4：推荐系统

- [x] P4-1 ChromaDB 集成（collection 创建、持久化配置）
- [x] P4-2 Embedding 模型封装（sentence-transformers）
- [x] P4-3 定时训练任务（APScheduler，每小时：SQLite → embedding → ChromaDB）
- [x] P4-4 `POST /api/recommend` 接口（embedding → ChromaDB 相似度搜索 → 聚合标签）
- [x] P4-5 模型版本追踪（写入 br_model_versions 表）
- [x] P4-6 单元测试：embedding 编码、相似度计算、推荐结果

## 已完成 ✅ — Phase 5：后台管理接口

- [x] P5-1 用户登录/登出接口
- [x] P5-2 书签 CRUD（列表分页、详情、编辑、删除）
- [x] P5-3 审计日志查询接口
- [x] P5-4 模型训练状态查询 + 手动触发训练
- [x] P5-5 敏感操作二次验证（踢人、删除等）

## 已完成 ✅ — Phase 6：前端后台管理

- [x] P6-1 前端项目配置（Tailwind 主题、黑白灰配色、日夜切换）
- [x] P6-2 Layout 布局（侧边栏菜单 + 顶栏 + 内容区，参考 javaex 结构）
- [x] P6-3 i18n 初始化（vue-i18n，中/英文）
- [x] P6-4 登录页面
- [x] P6-5 Dashboard（数据概览）
- [x] P6-6 书签管理页面（列表、搜索、编辑、推荐）
- [x] P6-7 审计日志页面
- [x] P6-8 模型状态页面（训练进度、手动触发）
- [x] P6-9 统一 API 请求层 + toast 错误提示
- [x] P6-10 Vitest 单元测试（核心组件）

## 已完成 ✅ — Phase 7：规范与质量

- [x] P7-1 三套环境配置（.env.development / .env.staging / .env.production）
- [x] P7-2 后端测试覆盖率 ≥ 80%
- [x] P7-3 前端 lint + build 通过
- [x] P7-4 依赖安全扫描（npm audit）
- [x] P7-5 Docker Compose 一键启动验证
- [x] P7-6 README 完善（部署方案、配置说明、API 文档）

## 已完成 ✅ — v0.1.1：UI 重设计（2026-05-04）

- [x] SVG Logo（亮/暗，黑白灰，字母 C 居中）✅ 2026-05-04
- [x] AdminLayout 磨砂玻璃侧边栏 + 头部 ✅ 2026-05-04
- [x] Login 居中卡片布局 ✅ 2026-05-04
- [x] Dashboard 统计卡片设计 ✅ 2026-05-04
- [x] Bookmarks/Audit/Model 页面改进 ✅ 2026-05-04
- [x] favicon + i18n「蠢人书签」✅ 2026-05-04
- [x] 中/英文切换 + 日夜切换 ✅ 2026-05-04

## 已完成 ✅ — v0.1.2：书签管理 CRUD 增强（2026-05-04）

- [x] 新增书签弹窗表单 ✅ 2026-05-04
- [x] 导入浏览器书签（Netscape HTML 格式，支持 Chrome/Firefox/Edge/Safari/Opera）✅ 2026-05-04
- [x] 导出用户书签为 JSON 文件 ✅ 2026-05-04
- [x] 隐藏 ingest 抓取入口 ✅ 2026-05-04
- [x] i18n 中/英文完整覆盖 ✅ 2026-05-04

## 待完成

- [ ] 补充前端测试用例（Vitest，覆盖率 ≥ 80%）
- [ ] 补充后端测试用例（安全模块覆盖率 ≥ 80%）
- [ ] ESLint 配置完善

## 已完成 ✅ — Phase 8：发布

- [x] P8-1 自动 commit: `chore(release): v0.1.0`
- [x] P8-2 feat 分支合并回 dev
- [x] P8-3 dev 合并到 main，打 tag `v0.1.0`
- [x] P8-4 切回 dev 分支
- [x] P8-5 更新 MAINTAIN.md 记录 v0.1.0 发布内容

---

## 技术约束

- 所有密钥走 `.env`，绝不硬编码
- API 全部鉴权，敏感操作二次验证
- 所有输入校验 + 转义
- 统一错误码：`2000` 成功，`1001` Token过期，`1002` 权限不足
- 统一响应：`{code, message, data}`
- Conventional Commits 规范
- 每次迭代完自动 lint → build → 修复 → commit → push

## 数据存储

| 存储 | 用途 |
|---|---|
| SQLite | 业务数据（书签、用户、审计日志、模型版本追踪） |
| ChromaDB | 向量数据（embedding 相似度搜索） |
| 本地磁盘 | 训练出的模型文件持久化 |

## 分支策略

```
main (生产) ← dev (开发) ← feat/任务名
```
