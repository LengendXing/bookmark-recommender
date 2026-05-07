# Bookmark Recommender 维护日志

## v0.2.12 - 2026-05-07
### 变更内容
- API 管理页面 CRUD 改造：从只读展示升级为完整增删改查
- 新增 `br_api_routes` 数据表存储 API 路由元数据
- 后端新增 6 个 CRUD 端点：列表/详情/创建/编辑/删除/同步
- 同步端点：从 FastAPI 注册路由自动同步到数据库（手动路由不被覆盖）
- 前端新增路由表单弹窗（method 下拉/path 输入/summary/tags/description/enabled）
- 表格新增启用/禁用开关、来源标识（自动/手动）、编辑/删除操作按钮
- 分页支持（每页 10/20/50）
- 启动时自动初始同步

### 影响范围
- 后端：models/api_route.py（新增），schemas/api_route.py（新增），api/api_routes.py（新增 6 端点），main.py（注册路由 + 启动同步 + 版本号），models/__init__.py（导入 ApiRoute），migrations/005_create_api_routes.sql（新增）
- 前端：ApiManagement.vue（重写为完整 CRUD），api/index.ts（新增 5 个 API 函数），i18n/en.json + zh.json（新增 15+ keys）

### 功能列表
- API 路由列表（分页/过滤/搜索）
- 新增 API 路由（表单弹窗 + 唯一约束校验）
- 编辑路由元数据（summary/tags/description/enabled）
- 删除路由（确认弹窗）
- 同步路由（从 FastAPI 注册路由导入）
- 启用/禁用开关
- 来源标识（自动=系统同步 / 手动=用户创建）

## v0.2.11 - 2026-05-07
### 变更内容
- 书签批量操作：支持多选书签后批量删除
- 表格新增复选框列（表头全选/每行单选）
- 批量操作工具栏（显示已选数量 / 批量删除 / 取消选择）
- 分页/搜索自动清空选中状态
- 表格新增「分类」列（Title 和 Tags 之间，响应式隐藏）
- 完全移除收藏夹功能：删除 Collection 模型/API/Schema/数据表/前端侧栏/弹窗/i18n
- 批量移动和移动收藏夹功能同步移除
- 新增「API管理」页面：展示所有对外 API 端点（请求方式/路径/描述/模块）
- 后端新增 GET /api/admin/api-list 端点（管理员认证）
- 数据库迁移：删除 br_bookmarks.collection_id 列，删除 br_collections 表

### 影响范围
- 后端：api/admin.py（新增 api-list 端点），api/collections.py（删除），models/collection.py（删除），models/__init__.py（移除 Collection 导入），schemas/collection.py（删除），models/bookmark.py（删除 collection_id），schemas/bookmark.py（删除 BatchMoveRequest/BookmarkMove/collection_id），api/bookmarks.py（删除 batch-move/move 端点及 collection_id 筛选），main.py（移除 collections 路由），migrations/004_remove_collection_id.sql（新增）
- 前端：Bookmarks.vue（新增分类列/移除收藏夹侧栏/移除收藏夹弹窗/移除批量移动），ApiManagement.vue（新增页面），AdminLayout.vue（新增菜单项），main.ts（新增路由），api/index.ts（移除 collections 导出/新增 apiList），i18n/en.json + zh.json（移除 collections 块/新增 apiManagement 块）

### 功能列表
- 书签多选（全选/单选/取消选择）
- 批量删除（确认弹窗 → API 批量删除 → 自动刷新）
- 书签表格分类列展示
- API 管理页面（路径/方法/标签过滤 + 端点列表表格）
- 分页/搜索切换自动清空选中

## v0.2.10 - 2026-05-06
### 变更内容
- GitHub 开源项目 AI 分析：对已 Star 项目调用 AI 分析生成标签/摘要/分类
- GitHub 推荐引擎：基于用户标签画像搜索 GitHub 发现新项目
- 新增 `br_recommended_repos` 表存储推荐项目（含 AI 标签/摘要/评分/匹配标签）
- 后端新增 8 个端点：analyze-all / analyze-progress / generate-recommendations / recommendations-progress / recommendations/sse / recommendations / repos/{id}
- 新增后台分析线程（逐条分析，进度轮询）和推荐线程（按 Top-K 标签搜索）
- 新增每日定时推荐任务（APScheduler cron 凌晨 3:00）
- 前端新增标签页切换（Starred / Recommended）
- 前端新增分析/推荐进度弹窗（百分比进度条 + 轮询状态更新）
- 前端新增 RepoDetailDrawer 组件（右侧滑入，展示 AI 分析/AI 标签/README/完整元数据）
- 仓库名改为按钮触发抽屉，不再外链跳转 GitHub
- AI 分析结果（AI 标签/摘要）在 Starred 列表内联展示
- 推荐列表展示评分/匹配标签，未读项目高亮
- 推荐列表分页（每页 10/20/50）
- API 限流备注：GitHub Search API 30 req/min（认证用户），代码中每标签 1 页 10 条

### 影响范围
- 后端：api/github.py（新增分析/推荐/SSE/进度 endpoint），services/ai_service.py（新增 analyze_repo 函数族），services/github_service.py（新增 search_repos_by_topic），models/recommended_repo.py（新增），schemas/github.py（新增 RecommendedRepoOut），main.py（新增每日定时任务），migrations/002_add_repo_fields.sql + 003_create_recommended_repos.sql
- 前端：GitHubProjects.vue（标签页、分析/推荐按钮、进度弹窗、抽屉集成），RepoDetailDrawer.vue（新增组件），api/index.ts（新增 6 个 API 函数），i18n/en.json + zh.json（新增 30+ keys）
- 依赖：新增 APScheduler（后端定时任务）

### 功能列表
- AI 分析 Star 仓库（批量逐条分析 + 进度轮询）
- 推荐引擎（标签画像 → GitHub 搜索 → AI 评分推荐）
- SSE 推送 + API 拉取双通道
- 每日凌晨 3:00 定时推荐
- 推荐项目列表（分页/评分/标签展示）
- RepoDetailDrawer 详情组件
- 分析/推荐进度弹窗

## v0.2.9 - 2026-05-06
### 变更内容
- 新增开源项目管理模块：菜单在审计日志上方，独立页面
- 左侧账户列表（添加/删除 GitHub Token 账户）
- 添加账户弹窗（OAuth + Token 双 Tab，OAuth 为占位说明）
- 右侧开源项目表格展示（仓库名/所有者/描述/语言/Star数/Fork数）
- 后端新增 br_github_accounts 和 br_starred_repos 数据表
- GitHub API 服务（获取用户信息/Star 列表/同步/搜索）
- 导入/导出：JSON 文件批量导入（跳过已有），JSON 导出
- 搜索：常规关键词搜索 + AI 语义搜索（基于嵌入向量相似度）
- 一键分析按钮（UI 占位，功能待后续实现）
- 删除项目确认弹窗
- 完整 i18n 中英文翻译（github/开源项目管理）

### 影响范围
- 后端：models/github_account.py、starred_repo.py（新增），services/github_service.py（新增），schemas/github.py（新增），api/github.py（新增），services/embedding.py（新增 semantic_search），main.py（注册路由）
- 前端：GitHubProjects.vue（新增页面），AdminLayout.vue（新增菜单项），main.ts（新增路由），api/index.ts（新增 github API），i18n/en.json、zh.json（新增 github + nav.github 块）
- 依赖：python-multipart（已安装）

### 功能列表
- GitHub Token 账户管理（添加/删除）
- GitHub Star 仓库同步到本地
- 仓库列表（分页/搜索/语义搜索）
- JSON 导入导出
- 删除仓库
- 一键分析占位按钮

## v0.2.8 - 2026-05-06
### 变更内容
- 书签管理分页增强：新增每页条数选择器（10/20/50/100）
- 新增页码跳转功能（输入页码直接跳转）
- 新增分页信息显示（第 X / N 页）
- 新增 pagination 中英文 i18n 文案
- 分页按钮风格保持统一（rounded-lg / border / 现有样式）

### 影响范围
- 前端：Bookmarks.vue（分页区域重构），i18n/locales/en.json、zh.json（新增 pagination 块）
- pageSize 从 const 改为 ref，支持动态切换

### 功能列表
- 每页条数下拉选择（切换自动重置到第1页）
- 页码跳转输入框 + GO 按钮（回车或点击跳转）
- 当前页 / 总页数实时显示

## v0.2.7 - 2026-05-06
### 变更内容
- 全局路由加载进度条：菜单切换即时响应，非阻塞式路由跳转
- 五页面骨架屏加载态：Dashboard/Audit/Model/Settings/Bookmarks 数据加载时展示骨架屏
- 新增 SkeletonBox / SkeletonTable / SkeletonCard 基础骨架组件
- 新增 useLoading composable 管理全局加载状态
- 修复 Audit 页面翻页无效 bug（补充 watch(page, load)）
- 恢复管理员默认账号密码

### 影响范围
- 前端：AdminLayout.vue（全局加载条），main.ts（路由守卫），新增 components/SkeletonBox.vue、SkeletonTable.vue、SkeletonCard.vue，新增 composables/useLoading.ts
- 五个页面：Dashboard.vue、Audit.vue、Model.vue、Settings.vue、Bookmarks.vue
- 全局样式：main.css（非波纹式对角线渐变骨架屏动画）

### 功能列表
- 菜单点击瞬间切换，顶部0.5px细进度条动画（对角线渐变滑过，非波纹/音浪式）
- 骨架屏加载态：对角线渐变 shimmer 动画，非传统波纹式
- 骨架屏组件支持自定义宽高和圆角
### 变更内容
- AI 分析接入 Playwright 无头浏览器：分析书签前先实际访问 URL 抓取真实页面内容
- 新增 `scrape_page_sync()` 函数，使用 Playwright sync API 提取页面标题、描述、正文
- `_run_analysis()` 先抓取后分析，AI 基于真实网页内容生成标题/描述/标签/分类
- 修复 Anthropic SDK 0.97+ base_url 自动追加 /v1 导致的 404 问题
- 修复 `GET /analyze-progress` 路由被 `/{bookmark_id}` 拦截的问题（静态路由移到动态路由之前）

### 影响范围
- 后端：services/scraper.py（新增 Playwright 抓取），api/bookmarks.py（路由修复、分析流程改造），services/ai_service.py（Anthropic endpoint 兼容修复）
- 新增依赖：playwright>=1.49.0

### 功能列表
- Playwright 无头浏览器自动抓取网页内容
- AI 基于真实网页内容做归纳分析
- 进度条实时显示分析百分比

## v0.2.5 - 2026-05-05
### 变更内容
- 搜索框合并：常规搜索 + 智能搜索 → 单个输入框 + 前置下拉切换（常规搜索/智能搜索）
- 新增「一键分析」按钮：对缺少 AI 字段的历史书签批量调用 AI 分析补全
- 新增 `POST /api/bookmarks/analyze-all` 端点，查找 generated_title 为空的书签并批量分析更新
- 新增按钮样式修复：加上与导入/导出一致的 muted 圆角背景

### 影响范围
- 后端：api/bookmarks.py（新增 analyze-all 端点）
- 前端：Bookmarks.vue（搜索框合并、一键分析按钮、新增按钮样式）、api/index.ts、i18n/locales/*.json

### 功能列表
- 搜索模式切换（常规搜索 / 智能搜索），单输入框
- 一键分析（批量 AI 分析历史书签，补全生成字段）
- 新增按钮样式统一

## v0.2.4 - 2026-05-05
### 变更内容
- AI 服务支持双 provider：OpenAI Compatible / Claude Proxy (Anthropic)
- `br_system_config` 新增 `api_provider` 和 `ai_model` 配置项
- 新增 `POST /api/system-config/test` 端点，支持模型连接测试
- 新增 `POST /api/system-config/models` 端点，获取可用模型列表
- 系统配置页面新增 API Provider 下拉、Model 输入框、连接测试区域
- 修复 Settings.vue 中 Axios 响应拦截后双层 data 路径问题

### 影响范围
- 后端：api/system_config.py, services/ai_service.py
- 前端：Settings.vue, api/index.ts, i18n/locales/*.json

### 功能列表
- OpenAI / Anthropic 双 provider 切换
- 模型测试（下拉选模型 → 测试 → 展示成功/失败+Token 用量）
- 模型列表自动获取

## v0.2.2 - 2026-05-05
### 变更内容
- 新增 `br_collections` 表实现书签收藏夹管理（平铺式，无嵌套）
- Bookmark 表新增 `collection_id` 字段
- Collections CRUD API（创建/编辑/删除收藏夹，校验所有权）
- 书签列表支持按 `collection_id` 筛选
- 新增 `POST /api/bookmarks/{id}/move` 端点用于移动书签到收藏夹
- 前端新增收藏夹侧边栏（左栏）及收藏夹管理 UI
- 表格 Action 列新增移动收藏夹下拉选择框
- 新增 collections i18n 中英文文案

### 影响范围
- 后端：models/collection.py, schemas/collection.py, api/collections.py, api/bookmarks.py, main.py
- 前端：Bookmarks.vue, api/index.ts, i18n/locales/*.json

### 功能列表
- 收藏夹创建/编辑/删除
- 按收藏夹筛选书签
- 书签移动到收藏夹（或移除）

## v0.2.3 - 2026-05-05
### 变更内容
- 操作列按钮合并为三点（⋮）kebab 菜单，减少表格空间占用
- Kebab 菜单包含：移动到...、编辑、删除三个操作
- 移动到...居中弹窗展示收藏夹列表，选中即移动
- 编辑弹窗居中展示，预填所有字段
- 标题列截断优化：中文 ≤6 字符 + 省略号，英文 ≤2 单词 + 省略号
- 标签列恢复至标题列之后

### 影响范围
- 前端：Bookmarks.vue（新增 kebab 菜单、移动弹窗、编辑弹窗、标题截断函数）

### 功能列表
- 三点 kebab 菜单（点击展开/外部点击关闭）
- 移动到收藏夹居中弹窗
- 编辑书签居中弹窗
- 标题智能截断（中文6字/英文2词）

## v0.2.1 - 2026-05-05
### 变更内容
- 嵌入向量增强：利用 tags/generated_title/generated_description/page_text 丰富索引文本
- RecommendResult schema 扩展 description/category 字段
- 前端新增语义搜索 UI（智能搜索 + 相关度百分比展示）
- 补充 semanticSearch/semanticPlaceholder/relevance i18n 中英文文案

### 影响范围
- 后端：app/services/embedding.py, app/schemas/bookmark.py
- 前端：Bookmarks.vue, i18n/locales/*.json

### 功能列表
- 语义搜索（自然语言描述查找书签）
- 相关度分数展示
- 嵌入向量的语义信息更丰富

## v0.2.0 - 2026-05-04
### 变更内容
- 新增系统配置页面（AI 模型 API 地址 + API Key）
- 新增 `br_system_config` 表存储系统配置
- AI 服务模块（OpenAI 兼容接口），支持自定义 base_url
- 书签导入增强：解析浏览器文件夹路径、后天 AI 分析线程
- 书签表扩展 8 个新字段：folder_path, date_added, page_title, page_description, page_text, generated_title, generated_description, crawl_error
- 前端新增书签详情抽屉组件（右侧滑入）
- 书签列表标题改为按钮触发抽屉，不再直接跳转 URL
- 中英文 i18n 完整

### 影响范围
- 后端：models, schemas, api/bookmarks, api/system_config, services/ai_service, services/import_service, main.py
- 前端：Bookmarks.vue, BookmarkDrawer.vue, Settings.vue, AdminLayout.vue, main.ts, api/index.ts, i18n/*.json

### 功能列表
- 系统配置（AI API 配置）
- 书签导入（解析文件夹 + AI 分析）
- 书签详情抽屉
- 书签导出
