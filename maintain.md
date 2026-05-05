# Bookmark Recommender 维护日志

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
