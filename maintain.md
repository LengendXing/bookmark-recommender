# Bookmark Recommender 维护日志

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
