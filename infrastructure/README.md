# PAC Infrastructure

> Personal AI Company 的基础设施层

## 一、本地 Supabase

公司统一的本地数据库和存储服务。

### 1.1 服务信息

| 配置 | 值 |
|------|-----|
| API URL | `http://127.0.0.1:54321` |
| Studio | `http://127.0.0.1:54323` |
| DB 端口 | `54322` |
| Anon Key | 见 `~/.claude/secrets.env` |

### 1.2 启动方式

```bash
cd ~/usr/pac/infrastructure
npx supabase start
```

### 1.3 停止方式

```bash
cd ~/usr/pac/infrastructure
npx supabase stop
```

## 二、数据存储架构

```
┌─────────────────────────────────────────────────────┐
│                    Linear Issue                      │
│         (元数据 + 链接引用，管理视角入口)              │
└─────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   GitHub    │  │  Supabase   │  │  Supabase   │
│   (代码)    │  │    DB       │  │   Storage   │
│             │  │  (元数据)   │  │  (文件)     │
└─────────────┘  └─────────────┘  └─────────────┘
```

## 三、Storage Buckets

| Bucket | 用途 | 公开访问 |
|--------|------|----------|
| `artifacts` | 产品产物（原型图、截图）| 是 |
| `content` | 内容素材（图片、封面）| 是 |

## 四、数据库 Schema

### pac.bu_artifacts - 产物索引

记录各事业部的产出物。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| bu | TEXT | 事业部 (product/content/investment) |
| type | TEXT | 产物类型 |
| linear_issue_id | TEXT | 关联 Linear Issue |
| session_id | TEXT | 关联 Claude Session |
| storage_url | TEXT | 存储位置 URL |
| metadata | JSONB | 额外信息 |
| created_at | TIMESTAMPTZ | 创建时间 |

### pac.content_posts - 内容发布记录

记录内容事业部的发布数据。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| platform | TEXT | 平台 (xhs/bilibili/x) |
| post_url | TEXT | 发布链接 |
| title | TEXT | 标题 |
| content | TEXT | 文案 |
| images | TEXT[] | 图片 URL 数组 |
| linear_issue_id | TEXT | 关联 Linear Issue |
| published_at | TIMESTAMPTZ | 发布时间 |
| views | INT | 浏览量 |
| likes | INT | 点赞数 |
| comments | INT | 评论数 |
| tracked_at | TIMESTAMPTZ | 数据更新时间 |

## 五、Redis（消息队列）

轻量级消息队列，用于任务调度、进程间通信。

### 5.1 服务信息

| 配置 | 值 |
|------|-----|
| 地址 | `127.0.0.1:6379` |
| 配置文件 | `/opt/homebrew/etc/redis.conf` |
| 版本 | 8.4.0 |

### 5.2 启动/停止

```bash
# 启动（开机自启）
brew services start redis

# 停止
brew services stop redis

# 重启
brew services restart redis

# 测试连接
redis-cli ping  # 返回 PONG 表示正常
```

### 5.3 使用场景

| 场景 | 推荐方案 |
|------|---------|
| Node.js 任务队列 | BullMQ |
| Python 任务队列 | Celery + Redis |
| 简单 Pub/Sub | Redis 原生 PUBLISH/SUBSCRIBE |
| 分布式锁 | Redis SETNX |

### 5.4 Node.js 示例（BullMQ）

```typescript
import { Queue, Worker } from 'bullmq';

// 创建队列
const queue = new Queue('tasks', { connection: { host: '127.0.0.1', port: 6379 } });

// 添加任务
await queue.add('process-video', { videoId: '123' });

// 处理任务
const worker = new Worker('tasks', async (job) => {
  console.log(`Processing ${job.name} with data:`, job.data);
}, { connection: { host: '127.0.0.1', port: 6379 } });
```

## 六、文件结构

```
infrastructure/
├── README.md              # 本文件
├── supabase/
│   ├── config.toml        # Supabase 配置
│   └── migrations/        # 数据库迁移
│       └── 20260203_init_pac_schema.sql
├── redis/
│   └── README.md          # Redis 使用说明
```
