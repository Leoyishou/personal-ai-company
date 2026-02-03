---
name: db
description: "自然语言查询 Supabase 数据库。支持 AI50、PersonalDigitalCenter 和本地 Supabase。"
---

# Chat to Supabase

用自然语言查询 Supabase 数据库，自动生成并执行 SQL。

## 使用方式

```
/db [项目名] <自然语言查询>
```

## 项目别名

| 别名 | Project ID / 连接方式 | 说明 |
|------|------------|------|
| `ai50` (默认) | `ebgmmkaxuhawfrwryzia` | AI50 项目（云端） |
| `pdc` | `mwvsdfalfqblbqwnyqpn` | PersonalDigitalCenter（云端） |
| `local` | `localhost:6543` | 本地 Supabase |

## 本地 Supabase 配置

- **位置**: `~/.claude/services/supabase-local/`
- **Dashboard**: http://localhost:8000 (用户名: `supabase`, 密码: `l06STN9x9tY2IlQd`)
- **API URL**: http://localhost:8000
- **PostgreSQL**: localhost:6543 (通过 Supavisor 连接池)
- **直连 DB**: localhost:5432 (绕过连接池)
- **数据库**: postgres
- **用户**: postgres
- **密码**: p6Num7hrPR55MK5MLZ2xnl4xoXnyYB1b
- **ANON_KEY**: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyAgCiAgICAicm9sZSI6ICJhbm9uIiwKICAgICJpc3MiOiAic3VwYWJhc2UtZGVtbyIsCiAgICAiaWF0IjogMTY0MTc2OTIwMCwKICAgICJleHAiOiAxNzk5NTM1NjAwCn0.dc_X5iR_VP_qT0zsiyj_I_OZ2T9FtRU2BBNWN8Bu4GE
- **SERVICE_ROLE_KEY**: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyAgCiAgICAicm9sZSI6ICJzZXJ2aWNlX3JvbGUiLAogICAgImlzcyI6ICJzdXBhYmFzZS1kZW1vIiwKICAgICJpYXQiOiAxNjQxNzY5MjAwLAogICAgImV4cCI6IDE3OTk1MzU2MDAKfQ.DaYlNEoUrrEn2Ig7tqibS-PHK5vgusbcbo7X36XVt4Q

### 本地查询方式

对于 `local` 项目，使用 psql 直连：
```bash
PGPASSWORD=p6Num7hrPR55MK5MLZ2xnl4xoXnyYB1b psql -h localhost -p 6543 -U postgres -d postgres -c "SQL"
```

## 示例

1. **查询默认项目（AI50）**
```
/db 最近7天新增了多少用户
/db 统计每天的活跃用户数
/db 显示所有表
```

2. **指定项目**
```
/db pdc 最近的订阅记录
/db ai50 用户增长趋势
```

3. **复杂查询**
```
/db 按来源统计用户注册数，按数量降序排列
/db 找出最近30天没有活动的用户
```

## 执行流程

1. **解析项目** - 识别项目别名，默认 ai50
2. **加载 Schema** - 读取 `~/.claude/skills/chat-to-supabase/schemas/` 下的表结构（如有）
3. **生成 SQL** - 根据自然语言和 schema 生成 PostgreSQL 查询
4. **执行查询** - 调用 `mcp__supabase__execute_sql`
5. **格式化输出** - 表格或 JSON 形式展示结果

## 内置查询

| 命令 | 说明 |
|------|------|
| `/db tables` | 显示所有表 |
| `/db schema <表名>` | 显示表结构 |
| `/db count <表名>` | 统计表行数 |

## 注意事项

- 只支持 SELECT 查询，不执行 INSERT/UPDATE/DELETE
- 复杂查询建议先用 `/db schema` 确认表结构
- 查询结果超过 100 行会自动截断
- **Supabase JS SDK 默认只返回 1000 条记录**。如果需要获取大量数据（如 50000+ 条），必须：
  - 使用分批查询：`.range(offset, offset + batchSize - 1)` 循环获取
  - 或者直接用 SQL 在数据库端聚合统计，避免传输大量原始数据

## Schema 缓存

为了生成更准确的 SQL，可以在 `~/.claude/skills/chat-to-supabase/schemas/` 目录下放置表结构文件：

```
schemas/
  ai50.json       # AI50 项目的表结构
  pdc.json        # PersonalDigitalCenter 的表结构
```

格式示例：
```json
{
  "tables": {
    "users": {
      "columns": ["id", "email", "created_at", "source"],
      "description": "用户表"
    },
    "events": {
      "columns": ["id", "user_id", "event_type", "created_at"],
      "description": "用户事件表"
    }
  }
}
```

## 技术实现

调用 Supabase MCP 的 `execute_sql` 工具：

```
mcp__supabase__execute_sql(project_id, query)
```
