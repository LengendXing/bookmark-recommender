CREATE TABLE IF NOT EXISTS br_api_routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    method VARCHAR(10) NOT NULL,
    path VARCHAR(512) NOT NULL,
    summary VARCHAR(512) DEFAULT '',
    tags TEXT DEFAULT '[]',
    description TEXT DEFAULT '',
    enabled BOOLEAN DEFAULT 1,
    source VARCHAR(32) DEFAULT 'auto',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_api_route_method_path ON br_api_routes(method, path);
