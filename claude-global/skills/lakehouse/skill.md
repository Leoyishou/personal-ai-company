---
name: lake
description: "本地 Lakehouse 分析引擎 - 基于 DuckDB 的 OLAP 查询，支持 Parquet/CSV 文件分析，可从 Supabase CDC 同步数据。"
---

# Lakehouse 分析引擎

本地大数据分析层，基于 DuckDB 构建。与 Supabase（OLTP）互补，专注于 OLAP 分析场景。

## 使用方式

```
/lake <自然语言查询>
/lake sync <表名>           # 从 Supabase 同步数据
/lake import <文件路径>     # 导入 Parquet/CSV 文件
/lake tables                # 显示所有表
/lake schema <表名>         # 显示表结构
```

## 架构

```
PostgreSQL (Supabase)
    ↓ [CDC 同步 / 手动导入]
Parquet Files (~/.claude/services/lakehouse/data/)
    ↓
DuckDB (查询引擎)
    ↓
DuckDB MCP Server
    ↓
Claude Code (/lake 命令)
```

## 数据目录

| 路径 | 说明 |
|------|------|
| `~/.claude/services/lakehouse/data/lakehouse.db` | DuckDB 数据库文件 |
| `~/.claude/services/lakehouse/data/parquet/` | Parquet 数据文件 |
| `~/.claude/services/lakehouse/data/csv/` | CSV 数据文件 |

## 执行流程

### 查询流程

1. **解析命令** - 识别是查询、同步还是导入
2. **加载 DuckDB MCP** - 使用 `mcp__duckdb__*` 工具集
3. **执行查询** - 通过 MCP 执行 SQL
4. **格式化输出** - 表格或 JSON 形式展示结果

### 同步流程（/lake sync）

1. 从 Supabase 导出数据（使用 `mcp__supabase__execute_sql`）
2. 转换为 Parquet 格式
3. 导入 DuckDB

### 导入流程（/lake import）

支持直接导入：
- Parquet 文件：`/lake import ~/data/events.parquet`
- CSV 文件：`/lake import ~/data/users.csv`
- 目录：`/lake import ~/data/exports/` （批量导入）

## 示例

### 基础查询

```
/lake 显示所有表
/lake 统计 events 表的记录数
/lake 最近 7 天的事件按类型分组统计
```

### 复杂分析

```
/lake 用户留存分析，计算第 1、7、30 天留存率
/lake 按小时统计 API 调用量，找出峰值时段
/lake 对比本周和上周的活跃用户数
```

### 数据导入

```
/lake import ~/Downloads/analytics_export.parquet
/lake sync users    # 从 Supabase 同步 users 表
```

## DuckDB MCP 工具

通过 MCP 调用 DuckDB：

| 工具 | 说明 |
|------|------|
| `mcp__duckdb__read_query` | 执行 SELECT 查询 |
| `mcp__duckdb__write_query` | 执行写入操作（INSERT/CREATE） |
| `mcp__duckdb__list_tables` | 列出所有表 |
| `mcp__duckdb__describe_table` | 显示表结构 |

## 与 Supabase 的关系

| 场景 | 推荐工具 |
|------|----------|
| 实时查询单条记录 | `/db`（Supabase） |
| 简单 CRUD 操作 | `/db`（Supabase） |
| 大规模聚合分析 | `/lake`（DuckDB） |
| 历史数据分析 | `/lake`（DuckDB） |
| 跨表复杂 JOIN | `/lake`（DuckDB） |
| 文件数据分析 | `/lake`（DuckDB） |

## 配置

### MCP 配置（~/.claude.json）

```json
{
  "mcpServers": {
    "duckdb": {
      "command": "uvx",
      "args": [
        "mcp-server-duckdb",
        "--db-path",
        "/Users/liuyishou/.claude/services/lakehouse/data/lakehouse.db"
      ]
    }
  }
}
```

### 数据库初始化

首次使用时自动创建数据库。如需手动初始化：

```bash
duckdb ~/.claude/services/lakehouse/data/lakehouse.db
```

## 注意事项

- DuckDB 查询默认无行数限制（与 Supabase 的 1000 条不同）
- Parquet 格式推荐用于大数据量场景
- 复杂分析优先在 DuckDB 端完成聚合，避免传输大量原始数据
- 同步操作会覆盖目标表，注意数据备份

## Phase 2: CDC 实时同步（待实现）

计划使用 OLake 实现 PostgreSQL → Parquet 的 CDC 同步：

```bash
# 部署 OLake（待实现）
docker compose -f ~/.claude/services/olake/docker-compose.yml up -d
```

架构：
```
PostgreSQL WAL → OLake → Parquet → DuckDB
```
