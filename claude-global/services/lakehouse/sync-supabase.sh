#!/bin/bash
# xhs-account-ops Supabase → DuckDB 同步脚本
# 使用 DuckDB postgres_scanner 直连 PostgreSQL

set -e

# 配置
LAKEHOUSE_DIR="$HOME/.claude/services/lakehouse"
DUCKDB_FILE="$LAKEHOUSE_DIR/data/lakehouse.db"
LOG_FILE="$LAKEHOUSE_DIR/logs/sync.log"

# xhs-account-ops PostgreSQL 配置
PG_HOST="localhost"
PG_PORT="54322"
PG_USER="postgres"
PG_PASS="postgres"
PG_DB="postgres"

PG_CONN="host=${PG_HOST} port=${PG_PORT} user=${PG_USER} password=${PG_PASS} dbname=${PG_DB}"

# 创建目录
mkdir -p "$LAKEHOUSE_DIR/logs"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 全量同步所有表
sync_all() {
    log "=== xhs-account-ops → DuckDB Sync Started ==="

    duckdb "$DUCKDB_FILE" << 'EOSQL'
INSTALL postgres;
LOAD postgres;
ATTACH 'host=localhost port=54322 user=postgres password=postgres dbname=postgres' AS pg (TYPE POSTGRES, READ_ONLY);

-- 同步所有 public 表到 DuckDB
CREATE OR REPLACE TABLE xhs_agent_sessions AS SELECT * FROM pg.public.agent_sessions;
CREATE OR REPLACE TABLE xhs_agent_messages AS SELECT * FROM pg.public.agent_messages;
CREATE OR REPLACE TABLE xhs_cc_pending_projects AS SELECT * FROM pg.public.cc_pending_projects;
CREATE OR REPLACE TABLE xhs_project_milestones AS SELECT * FROM pg.public.project_milestones;
CREATE OR REPLACE TABLE xhs_session_content_links AS SELECT * FROM pg.public.session_content_links;
CREATE OR REPLACE TABLE xhs_cc_projects AS SELECT * FROM pg.public.cc_projects;
CREATE OR REPLACE TABLE xhs_cc_tasks AS SELECT * FROM pg.public.cc_tasks;
CREATE OR REPLACE TABLE xhs_ideas AS SELECT * FROM pg.public.xhs_ideas;
CREATE OR REPLACE TABLE xhs_series AS SELECT * FROM pg.public.xhs_series;
CREATE OR REPLACE TABLE xhs_research AS SELECT * FROM pg.public.xhs_research;
CREATE OR REPLACE TABLE xhs_copies AS SELECT * FROM pg.public.xhs_copies;
CREATE OR REPLACE TABLE xhs_images AS SELECT * FROM pg.public.xhs_images;
CREATE OR REPLACE TABLE xhs_publications AS SELECT * FROM pg.public.xhs_publications;
CREATE OR REPLACE TABLE xhs_evaluations AS SELECT * FROM pg.public.xhs_evaluations;
CREATE OR REPLACE TABLE xhs_session_task_links AS SELECT * FROM pg.public.session_task_links;

-- 记录同步时间
CREATE TABLE IF NOT EXISTS sync_metadata (
    sync_time TIMESTAMP,
    source VARCHAR,
    tables_synced INTEGER
);
INSERT INTO sync_metadata VALUES (NOW(), 'xhs-account-ops', 15);

-- 显示同步结果
SELECT
    table_name,
    estimated_size as rows
FROM duckdb_tables()
WHERE table_name LIKE 'xhs_%'
ORDER BY rows DESC;
EOSQL

    log "=== Sync Completed ==="
}

# 显示当前 DuckDB 中的表
show_tables() {
    duckdb "$DUCKDB_FILE" << 'EOSQL'
SELECT
    table_name,
    estimated_size as rows
FROM duckdb_tables()
WHERE table_name LIKE 'xhs_%' OR table_name LIKE 'local_%' OR table_name LIKE 'cc_%'
ORDER BY table_name;
EOSQL
}

# 查询同步历史
show_history() {
    duckdb "$DUCKDB_FILE" -c "SELECT * FROM sync_metadata ORDER BY sync_time DESC LIMIT 10;"
}

# 命令行参数处理
case "${1:-all}" in
    all)
        sync_all
        ;;
    show)
        show_tables
        ;;
    history)
        show_history
        ;;
    *)
        echo "Usage: $0 [all|show|history]"
        exit 1
        ;;
esac
