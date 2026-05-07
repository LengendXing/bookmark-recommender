CREATE TABLE IF NOT EXISTS br_api_call_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_id INTEGER,
    method VARCHAR(10) NOT NULL,
    path VARCHAR(512) NOT NULL,
    request_body TEXT DEFAULT '',
    response_status INTEGER DEFAULT 200,
    response_body TEXT DEFAULT '',
    duration_ms REAL DEFAULT 0,
    error TEXT DEFAULT '',
    user_id INTEGER,
    client_ip VARCHAR(45) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_call_logs_created ON br_api_call_logs(created_at);
