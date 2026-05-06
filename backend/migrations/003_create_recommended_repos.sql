-- 新建 AI 推荐项目表，存储系统自动挖掘的 GitHub 项目
CREATE TABLE IF NOT EXISTS br_recommended_repos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    repo_full_name VARCHAR(256) NOT NULL,
    repo_name VARCHAR(128) NOT NULL DEFAULT '',
    owner VARCHAR(128) NOT NULL DEFAULT '',
    html_url TEXT NOT NULL DEFAULT '',
    clone_url TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    ai_summary TEXT NOT NULL DEFAULT '',
    topics TEXT NOT NULL DEFAULT '',
    ai_tags TEXT NOT NULL DEFAULT '',
    language VARCHAR(64) NOT NULL DEFAULT '',
    language_color VARCHAR(16) NOT NULL DEFAULT '',
    stars INTEGER NOT NULL DEFAULT 0,
    forks INTEGER NOT NULL DEFAULT 0,
    open_issues INTEGER NOT NULL DEFAULT 0,
    watchers INTEGER NOT NULL DEFAULT 0,
    license VARCHAR(64) NOT NULL DEFAULT '',
    homepage TEXT NOT NULL DEFAULT '',
    default_branch VARCHAR(64) NOT NULL DEFAULT '',
    size_kb INTEGER NOT NULL DEFAULT 0,
    archived BOOLEAN NOT NULL DEFAULT 0,
    score REAL NOT NULL DEFAULT 0.0,
    recommend_reason TEXT NOT NULL DEFAULT '',
    match_tags TEXT NOT NULL DEFAULT '',
    source_tag VARCHAR(128) NOT NULL DEFAULT '',
    is_read BOOLEAN NOT NULL DEFAULT 0,
    is_starred BOOLEAN NOT NULL DEFAULT 0,
    recommended_at VARCHAR(64),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_recommended_repo ON br_recommended_repos(user_id, repo_full_name);
CREATE INDEX IF NOT EXISTS ix_rec_user_read ON br_recommended_repos(user_id, is_read);
CREATE INDEX IF NOT EXISTS ix_rec_user_time ON br_recommended_repos(user_id, recommended_at);
