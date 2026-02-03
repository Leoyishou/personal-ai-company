---
name: projects
description: "项目管理工具 - 查看和管理项目状态，追踪最近的 coding 活动。"
---

# /projects - 项目管理 Skill

查看和管理项目状态，追踪最近的 coding 活动。

## 目录体系

工作区根目录：`/Users/liuyishou/usr/`

```
/Users/liuyishou/usr/
├── projects/      # 代码项目
│   ├── inbox/     # 收集箱（新项目入口）
│   ├── wip/       # 活跃开发（当前在写的）
│   ├── polish/    # 打磨中（功能完成，优化细节）
│   ├── published/ # 已发布
│   └── archive/   # 搁置
└── odyssey/       # 数字化管理系统 (Obsidian)
    ├── 0 收集箱/
    ├── 1 一切皆项目/  # 项目卡片
    ├── 2 第二大脑/
    └── ...
```

**代码项目目录**：`/Users/liuyishou/usr/projects/`

| 目录 | 含义 | 说明 |
|------|------|------|
| `inbox/` | 收集箱 | 新项目默认入口 |
| `wip/` | 活跃开发 | 当前正在写代码的项目 |
| `polish/` | 打磨中 | 功能基本完成，优化细节 |
| `published/` | 已发布 | 上线/发布的项目 |
| `archive/` | 搁置 | 暂停或放弃的项目 |

**odyssey 关联**：`/Users/liuyishou/usr/odyssey/`

代码项目在 odyssey 里有对应的项目卡片（.md），记录思考和规划。

### 目录对应关系

| projects/ | odyssey/ | 说明 |
|-----------|----------|------|
| `inbox/` | `0 收集箱/repo/` | 新收集的代码项目 |
| `wip/` | `1 一切皆项目/wip/` | 活跃开发中 |
| `polish/` | `1 一切皆项目/进行中/` | 打磨阶段 |
| `published/` | `1 一切皆项目/已结项/` | 已发布 |
| `archive/` | `1 一切皆项目/搁置中/` | 搁置 |

### 项目卡片格式

```markdown
---
type: code-project
path: /Users/liuyishou/usr/projects/wip/VoiceType
status: wip
tags:
  - app
  - macos
created: 2026-01-27
---
# 项目名

简要描述

## 想法
- ...

## 进展
- 2026-01-27 xxx
```

### 同步规则

当执行 `mv <项目> <目录>` 时：
1. 移动代码目录
2. 更新卡片 frontmatter 的 `path:` 和 `status:`
3. 移动卡片到对应的 odyssey 目录

生命周期流转：
```
inbox → wip → polish → published
  ↘      ↘      ↘
         archive
```

## 命令一览

### 基础命令
| 命令 | 功能 |
|------|------|
| `/projects` | 项目概览（按目录分组） |
| `/projects <目录>` | 列出该目录所有项目 |
| `/projects <项目名>` | 查看项目详情和 git 活动 |
| `/projects mv <项目> <目录>` | 移动项目到指定目录 |

### 信息增强
| 命令 | 功能 |
|------|------|
| `/projects health` | 健康检查：未提交更改、过期依赖、长期未更新 |
| `/projects stats <项目>` | 项目统计：代码行数、语言构成、文件数 |
| `/projects readme <项目>` | 快速预览项目 README |

### 自动化
| 命令 | 功能 |
|------|------|
| `/projects cleanup` | inbox 清理建议：超过 30 天未动的项目 |
| `/projects active` | 按 git commit 频率排序的活跃项目 |
| `/projects new <模板>` | 从模板创建新项目 |

### 集成联动
| 命令 | 功能 |
|------|------|
| `/projects linear <项目>` | 查看关联的 Linear issues |
| `/projects github <项目>` | 查看 GitHub 远程状态、PR、stars |
| `/projects release <项目>` | 查看发布状态（TestFlight/npm） |

### 搜索发现
| 命令 | 功能 |
|------|------|
| `/projects search <关键词>` | 跨项目搜索代码 |
| `/projects tag <项目> <标签>` | 给项目打标签 |
| `/projects find <模糊词>` | 模糊匹配项目（支持别名和中文） |

### 回顾复盘
| 命令 | 功能 |
|------|------|
| `/projects weekly` | 周报：本周各项目 commit 汇总 |
| `/projects timeline` | 时间线：项目创建/发布历史 |

---

## 执行步骤

### /projects（无参数）- 项目概览 + 操作建议

**触发词**：「项目」「projects」

**优先读取缓存**：每晚 23:50 自动生成缓存，触发时直接读取。

```bash
CACHE_FILE="/Users/liuyishou/.claude/skills/projects/cache.json"
METADATA_FILE="/Users/liuyishou/.claude/skills/projects/metadata.json"

# 读取缓存
cat "$CACHE_FILE"
# 读取描述
cat "$METADATA_FILE"
```

**输出时显示缓存时间**：在标题后标注 `(数据更新于 YYYY-MM-DD HH:MM)`

---

**手动刷新缓存**（仅在需要最新数据时）：
```bash
/Users/liuyishou/.claude/skills/projects/generate-cache.sh
```

---

**缓存内容包含**：
- `generated_at`: 缓存生成时间
- `recent_active`: 最近 3 天有 commit 的项目
- `directories`: 各目录的项目列表（最多 10 个）
- `stats`: 各目录项目数量统计

**定时任务顺序**（crontab）：
- 23:05 - projects-odyssey 同步
- 23:10 - 项目描述更新
- 23:50 - **缓存生成**（在描述更新之后）

**输出格式**：

```
## 最近 3 天活跃

| 项目 | 目录 | 最近动态 | 时间 |
|------|------|---------|------|
| VoiceType | wip | Initial commit: macOS 语音转文本应用 | 1 天前 |
| personal-ai-company | published | 优化 readme | 2 天前 |
| personal-ai-agent | inbox | Add dashboard screenshot | 3 天前 |

---

## 项目概览

### wip（活跃开发）
| 项目 | 描述 |
|------|------|
| VoiceType | macOS 语音转文本应用，按住说话松开输入 |

### polish（打磨中）
| 项目 | 描述 |
|------|------|
| daily-quote-app | Expo/React Native 应用 |
| dejavu | iOS app combining three layers |

### inbox（36 个，最近 5 个）
| 项目 | 描述 |
|------|------|
| supabase-ai50 | 无描述 |
| idea-spark | 无描述 |
| curated-daily-edge | Supabase Edge Functions 迁移 |
...

### published（已发布）
| 项目 | 描述 |
|------|------|
| personal-ai-company | 如果强迫让你每天消耗 1 亿 token... |
| vocab-highlighter | 浏览网页时自动标记生词 |
| ModelHop | Forward prompts between AI models |

---

## 可用操作
- 「VoiceType」→ 查看项目详情和 git 活动
- 「mv idea-spark wip」→ 移动到活跃开发
- 「health」→ 检查未提交代码和过期依赖
- 「cleanup」→ 查看 inbox 清理建议
- 「weekly」→ 生成本周 commit 周报
- 「update-desc」→ 刷新所有项目描述
```

**关键**：
1. **先展示最近 3 天活跃项目**，让用户快速了解近期在忙什么
2. 再展示按目录分组的完整概览
3. 描述来自 `metadata.json`，优先从 README/package.json 自动提取

### /projects <项目名> - 查看项目详情

1. 先定位项目路径
2. 显示基本信息 + git 活动

```bash
# 定位项目
find "$PROJ_ROOT" -maxdepth 2 -type d -name "<项目名>" | head -1

# Git 活动
cd <项目路径>
git log --oneline -10 --format="%h %s (%ar)"
git status --short
```

### /projects mv <项目> <目标目录> - 移动项目

```bash
# 找到项目当前位置
SRC=$(find "$PROJ_ROOT" -maxdepth 2 -type d -name "<项目>" | head -1)
mv "$SRC" "$PROJ_ROOT/<目标目录>/"
```

### /projects health - 健康检查

扫描所有项目：

```bash
for proj in $(find "$PROJ_ROOT" -maxdepth 2 -mindepth 2 -type d); do
  # 检查未提交更改
  if [ -d "$proj/.git" ]; then
    changes=$(git -C "$proj" status --porcelain 2>/dev/null | wc -l)
    if [ $changes -gt 0 ]; then
      echo "[未提交] $proj ($changes 个文件)"
    fi

    # 检查最后 commit 时间
    last_commit=$(git -C "$proj" log -1 --format=%cr 2>/dev/null)
    echo "$proj: $last_commit"
  fi

  # 检查过期依赖（如果有 package.json）
  if [ -f "$proj/package.json" ]; then
    # npm outdated --json
  fi
done
```

输出格式：
```
## 需要关注
- [未提交] VoiceType (3 个文件待提交)
- [过期依赖] mcp-dashboard (5 个包需更新)
- [长期未动] douban (45 天前)

## 健康项目
- idea-spark (2天前, 无未提交)
- daily-quote-app (3天前, 无未提交)
```

### /projects stats <项目> - 项目统计

```bash
cd <项目路径>
# 代码行数和语言
cloc . --quiet 2>/dev/null || find . -name "*.ts" -o -name "*.js" -o -name "*.py" | xargs wc -l

# 文件数
find . -type f | wc -l

# Git 统计
git shortlog -sn --all 2>/dev/null
```

### /projects cleanup - inbox 清理建议

```bash
# 找出 30 天未修改的 inbox 项目
find "$PROJ_ROOT/inbox" -maxdepth 1 -type d -mtime +30
```

输出：
```
## 建议归档 (超过30天未动)
- douban (45天)
- fasong (40天)

执行 `/projects mv douban archive` 归档
```

### /projects weekly - 周报生成

```bash
for proj in $(find "$PROJ_ROOT" -maxdepth 2 -mindepth 2 -type d -name ".git" -exec dirname {} \;); do
  commits=$(git -C "$proj" log --oneline --since="1 week ago" 2>/dev/null | wc -l)
  if [ $commits -gt 0 ]; then
    echo "## $(basename $proj) ($commits commits)"
    git -C "$proj" log --oneline --since="1 week ago"
  fi
done
```

---

## 数据存储

### 项目元数据
`~/.claude/skills/projects/metadata.json`

```json
{
  "VoiceType": {
    "alias": ["语音输入", "voice", "语音那个"],
    "tags": ["#app", "#ios", "#tool"],
    "desc": "语音转文字输入法 App",
    "linear_project": "PROJECT_ID",
    "github": "liuyishou/VoiceType"
  }
}
```

### 项目模板
`~/.claude/skills/projects/templates/`

```
templates/
├── expo-app/       # React Native/Expo 模板
├── nextjs/         # Next.js 模板
├── python-cli/     # Python CLI 工具模板
└── skill/          # Claude Skill 模板
```

---

## 项目描述管理

### 描述来源优先级

1. **手动设置**：`metadata.json` 中 `descSource: "manual"` 的描述不会被覆盖
2. **package.json**：`description` 字段
3. **README.md**：第一段非标题文字
4. **pyproject.toml / Cargo.toml**：`description` 字段
5. **结构猜测**：根据文件结构推断项目类型

### 更新描述

**手动触发**：
```bash
node ~/.claude/skills/projects/update-descriptions.mjs
```

**定时更新**（每天 23:00）：
已配置 crontab：
```
0 23 * * * cd ~/.claude/skills/projects && node update-descriptions.mjs >> /tmp/projects-desc.log 2>&1
```

### /projects update-desc - 刷新描述

执行脚本更新所有项目描述：
```bash
node ~/.claude/skills/projects/update-descriptions.mjs
```

输出示例：
```
[更新] VoiceType: macOS 语音转文本应用...
[更新] idea-spark: AI 灵感捕捉工具...

✅ 更新了 5 个项目描述
⚠️ 12 个项目没有描述
```

### 手动编辑描述

直接编辑 `metadata.json`，设置 `descSource: "manual"` 防止被覆盖：
```json
{
  "idea-spark": {
    "desc": "AI 驱动的灵感捕捉和知识管理工具",
    "descSource": "manual"
  }
}
```

---

## 模糊匹配逻辑

当用户输入不完全匹配时：

1. 精确匹配项目名
2. 匹配别名（alias）
3. 匹配标签（tags）
4. 模糊搜索项目名（包含关系）
5. 搜索 README 内容

示例：
- 「语音那个」→ VoiceType（通过别名）
- 「#app」→ 列出所有带 #app 标签的项目
- 「voice」→ VoiceType（模糊匹配）
