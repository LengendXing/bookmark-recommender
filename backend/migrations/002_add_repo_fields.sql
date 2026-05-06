-- 扩展 br_starred_repos 表字段，用于存储 GitHub API 详细信息和 AI 分析结果
ALTER TABLE br_starred_repos ADD COLUMN language_color VARCHAR(16) NOT NULL DEFAULT '';
ALTER TABLE br_starred_repos ADD COLUMN open_issues INTEGER NOT NULL DEFAULT 0;
ALTER TABLE br_starred_repos ADD COLUMN watchers INTEGER NOT NULL DEFAULT 0;
ALTER TABLE br_starred_repos ADD COLUMN size_kb INTEGER NOT NULL DEFAULT 0;
ALTER TABLE br_starred_repos ADD COLUMN topics TEXT NOT NULL DEFAULT '';
ALTER TABLE br_starred_repos ADD COLUMN homepage TEXT NOT NULL DEFAULT '';
ALTER TABLE br_starred_repos ADD COLUMN license VARCHAR(64) NOT NULL DEFAULT '';
ALTER TABLE br_starred_repos ADD COLUMN default_branch VARCHAR(64) NOT NULL DEFAULT '';
ALTER TABLE br_starred_repos ADD COLUMN archived BOOLEAN NOT NULL DEFAULT 0;
ALTER TABLE br_starred_repos ADD COLUMN readme_text TEXT NOT NULL DEFAULT '';
ALTER TABLE br_starred_repos ADD COLUMN ai_tags TEXT NOT NULL DEFAULT '';
ALTER TABLE br_starred_repos ADD COLUMN ai_summary TEXT NOT NULL DEFAULT '';
ALTER TABLE br_starred_repos ADD COLUMN ai_category VARCHAR(64) NOT NULL DEFAULT '';
ALTER TABLE br_starred_repos ADD COLUMN ai_analyzed_at VARCHAR(64);
ALTER TABLE br_starred_repos ADD COLUMN analyze_error TEXT NOT NULL DEFAULT '';
