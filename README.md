# Personal AI Company

**一家全员 AI 的公司，你是唯一的人类——老板**

---

## 一、全员 AI，只有老板是人

你拥有一家公司。

公司里没有人类员工，所有部门都由 AI 驱动：

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR PERSONAL AI COMPANY                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│     👤 CEO (你)                                                  │
│      │                                                           │
│      ├─→ 📢 公关部：发推文、发小红书、做声量                      │
│      ├─→ 🔬 战投部：行业调研、竞品分析、投资研报                  │
│      ├─→ 💻 研发部：写代码、做产品、发布应用                      │
│      ├─→ 🎬 内容部：下载素材、剪辑视频、生成图片                  │
│      └─→ 📊 运营部：数据监控、定时任务、流程自动化                │
│                                                                  │
│     全员 AI，7×24 在线，永不请假，随叫随到                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**你的工作方式变了**：

| 传统模式 | AI 公司模式 |
|---------|------------|
| 自己写推文 | 下达指令："公关部，发一条关于 AI 趋势的推" |
| 自己做调研 | 下达指令："战投部，调研一下 AI 视频赛道" |
| 自己剪视频 | 下达指令："内容部，把这个素材做成短视频" |
| 凡事亲力亲为 | **只做决策，执行交给 AI** |

---

## 二、公司运营模式

### 2.1 模式一：即时指令

CEO 随时可以下达命令，AI 立即执行。

```
你（Telegram）：公关部，发条推，内容是"Claude Code 真好用"
AI：[公关部] 收到，正在执行...
AI：[公关部] 完成：推文已发布 https://x.com/...
```

**适合**：突然想到的事，让对应部门马上去做。

### 2.2 模式二：自动巡检

每 30 分钟，AI 自动检查你的"CEO 待办清单"（滴答清单），各部门领取任务：

```
AI：老板，各部门汇报：

    📢 公关部完成 1 项：
    ✅ 发推：今天学到的 3 个技巧 → https://x.com/...

    🎬 内容部完成 1 项：
    ✅ 下载视频：xxx.mp4 → ~/Downloads/

    ⏭️ 待定 1 项（需要更多信息）：
    - "洗稿发小红书" → 请问洗哪篇内容？
```

**适合**：把想法随手丢进清单，让公司在后台自动运转。

---

## 三、公司总部 Dashboard

访问 **http://localhost:5050** 进入公司管理后台。

![Dashboard Screenshot](./assets/dashboard.png)

**管理功能**：
- 📊 **经营数据** - 任务完成数、成功率、本周趋势
- 📜 **实时动态** - 各部门正在做什么（WebSocket 实时推送）
- 📋 **执行记录** - 所有已完成任务的状态和结果
- 🎯 **CEO 直通车** - 在网页直接下达指令

---

## 四、为什么是"公司"而不是"助理"？

### 4.1 思维模式的本质区别

```
"AI 助理"思维              "AI 公司"思维
     ↓                           ↓
 一个人帮你做事              一个组织为你运转
     ↓                           ↓
  你是用户                    你是 CEO
     ↓                           ↓
  被动响应                    主动运营
     ↓                           ↓
  工具属性                    资产属性
```

### 4.2 "公司"意味着什么？

**1. 组织架构**
- 不是一个万能助理，而是多个专业部门
- 每个部门有明确的职责边界
- 任务自动路由到合适的部门

**2. 持续运转**
- 公司不会因为 CEO 睡觉而停摆
- 7×24 在线，自动处理可自动化的任务
- 你醒来时，工作已经完成

**3. 可扩展**
- 随时可以"成立新部门"（添加新能力）
- 部门之间可以协作
- 公司能力随着你的需求增长

### 4.3 技术实现：LLM + 图灵机

```
LLM（大语言模型）     +     图灵机（计算机）
       ↓                         ↓
   理解、推理、创作           7×24 不间断执行
       ↓                         ↓
   "各部门的大脑"            "公司的躯体"
       ↓                         ↓
       └──────────┬──────────────┘
                  ↓
            你的 AI 公司
```

---

## 五、系统架构

### 5.1 有状态 vs 无状态

**整个公司只有一个有状态服务——CEO 助理**，其他都是无状态的临时工。

```
┌─────────────────────────────────────────────────────────────────┐
│                    CEO 助理 (有状态服务)                          │
│                                                                  │
│  Agent: ceo-assistant                                            │
│  Session: 9826a95e-9bf8-4116-8d6e-70f8a1a7dfd8                  │
│  存储: ~/.claude/projects/.../xxx.jsonl                          │
│                                                                  │
│  特点：                                                          │
│  - 永久上下文，记得所有对话历史                                    │
│  - 了解老板的偏好、习惯、之前做过的事                              │
│  - 所有入口（Web/Telegram/定时）都是同一个"人"在响应               │
├─────────────────────────────────────────────────────────────────┤
│                         入口层                                    │
│                                                                  │
│  [Web Dashboard]  →  /api/chat  ─┐                               │
│  [Telegram 消息]  →  scheduler  ─┼──→ 同一个 CEO 助理 Session     │
│  [定时扫描]       →  scheduler  ─┘                               │
├─────────────────────────────────────────────────────────────────┤
│                      执行层 (无状态)                              │
│                                                                  │
│  CEO 助理根据任务类型，临时拉起子进程：                            │
│                                                                  │
│  ├─ 公关部 (haiku): 发推、发小红书 → 执行完即销毁                  │
│  ├─ 内容部 (sonnet): 生成图片、下载视频 → 执行完即销毁             │
│  └─ 战投部 (opus): 深度调研、分析 → 执行完即销毁                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 为什么这样设计？

| 设计 | 原因 |
|------|------|
| **CEO 助理有状态** | 你和助理是长期关系，它需要记得之前的对话、你的偏好 |
| **各部门无状态** | 具体任务不需要记忆，执行完就结束，省钱省资源 |
| **单一 Session** | 无论从哪个入口（Web/Telegram/定时），都是同一个"人"在响应 |

### 5.3 技术实现

```bash
# CEO 助理调用方式（有状态）
claude --agent ceo-assistant --resume <session-id> -p "扫描滴答清单"

# 各部门调用方式（无状态）
claude -p "发推：xxx" --model haiku  # 公关部，执行完即销毁
```

**关键文件：**

| 文件 | 作用 |
|------|------|
| `~/.claude/agents/ceo-assistant.md` | CEO 助理的角色定义、能力、指令 |
| `~/.claude/skills/personal-assistant/ceo-session.json` | Session ID 配置备份 |
| `~/.claude/projects/.../xxx.jsonl` | 对话历史存储（会越来越大） |

### 5.4 调度流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    Personal AI Company                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  总调度中心 (scheduler.py) - 常驻运行                    │    │
│  │  ├─ 监听 CEO 指令（Telegram）→ 转发给 CEO 助理           │    │
│  │  ├─ 每 30 分钟巡检待办清单 → CEO 助理判断和执行          │    │
│  │  └─ 所有请求都通过同一个 Session                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│                            ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  CEO 助理（有状态，永久驻留）                             │    │
│  │  ├─ 理解任务，判断可执行性                               │    │
│  │  ├─ 路由到合适的部门（选择模型）                         │    │
│  │  ├─ 启动子 Agent 执行具体任务                            │    │
│  │  └─ 汇总结果，通过 Telegram 汇报                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│                            ↓ 临时拉起                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  各部门执行层（无状态，用完即毁）                         │    │
│  │  ├─ 公关部 (haiku): 发推、发小红书                       │    │
│  │  ├─ 内容部 (sonnet): 生成图片、处理素材                  │    │
│  │  └─ 战投部 (opus): 深度调研、分析报告                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 六、搭建你的 AI 公司

### 6.1 公司基础设施

| 你需要准备的 | 公司类比 | 作用 |
|-------------|---------|------|
| **Mac 电脑** | 办公大楼 | 公司 7×24 运转的物理载体 |
| **[Amphetamine](https://apps.apple.com/app/amphetamine/id937984704)** | 大楼的电力系统 | 防止 Mac 休眠，确保永不断电（免费） |
| **[Claude Code Max](https://claude.com/download)** | 校招预算 | 雇佣 AI 员工的薪资（$100/月或$200/月） |
| **[Telegram](https://telegram.org/)** | 飞书 | 你和公司的沟通渠道 |
| **[滴答清单](https://dida365.com/)** | CEO 脑海里的想法 | 公司定期扫描，自动执行可执行的任务 |
| **[X (Twitter)](https://x.com/)** | 海外公关部 | AI 帮你发推文、做海外声量 |
| **[小红书](https://www.xiaohongshu.com/)** | 国内公关部 | AI 帮你发笔记、做国内声量 |
| **股票账户** | 战投部的仓位 | AI 帮你监控持仓、分析研报（可选） |
| **[Xcode](https://developer.apple.com/xcode/)** | 研发部的工位 | AI 帮你开发 iOS/Mac 应用 |
| **[Apple Developer](https://developer.apple.com/)** | 研发部的上架资质 | AI 帮你把应用发布到 App Store（$99/年） |
| **[Chrome 开发者](https://chrome.google.com/webstore/devconsole)** | 研发部的浏览器渠道 | AI 帮你开发和发布 Chrome 插件（$5 一次性） |
| **Python / Node.js** | 研发部的工具链 | AI 写代码、跑脚本的基础环境 |
| **[Supabase](https://supabase.com/)** | 后端研发 + DBA + OPS | 数据库、认证、存储，后端基础设施一站式搞定 |

> **重要**：Mac 休眠后 launchd 服务会暂停。安装 Amphetamine 并设置「Indefinitely」保持唤醒，确保公司 24/7 在线。

### 6.2 安装步骤

```bash
# Step 1: 克隆公司模板
git clone https://github.com/Leoyishou/personal-ai-company.git
cd personal-ai-company

# Step 2: 复制配置
cp .env.example .env

# Step 3: 填写各部门凭证
nano .env

# Step 4: 启动公司
./install.sh

# Step 5: 验证运行
launchctl list | grep personal-ai
```

---

## 七、配置指南

### 7.1 CEO 专线（必填）

用于接收汇报 + 下达指令。

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+8613800138000
```

**获取方式**：https://my.telegram.org/apps

### 7.2 CEO 待办（必填）

公司自动巡检的任务来源。

```env
DIDA365_CLIENT_ID=your_client_id
DIDA365_CLIENT_SECRET=your_client_secret
```

**获取方式**：https://developer.dida365.com/

### 7.3 各部门凭证（按需）

```env
# 公关部 - 发推文
X_API_KEY=...
X_ACCESS_TOKEN=...

# 战投部 - AI 调研
OPENROUTER_API_KEY=...

# 公关部 - 小红书
XHS_COOKIE=...
```

---

## 八、CEO 指令示例

### 8.1 即时指令（Telegram）

```
公关部，发条推：今天天气真好
内容部，下载这个视频 https://youtube.com/watch?v=xxx
战投部，调研一下 React 19 新特性
内容部，生成一张图：赛博朋克风格的猫
```

### 8.2 待办清单格式

**好的指令（部门能执行）**：
```
发推：具体的推文内容
下载视频：https://youtube.com/xxx
调研：React 19 有哪些新特性
```

**模糊的指令（部门会请示）**：
```
发两条  ← 发什么内容？
洗稿  ← 洗哪篇？
做视频  ← 什么主题？
```

---

## 九、公司目录结构

```
~/.claude/
├── skills/personal-assistant/
│   ├── SKILL.md              # 部门职责与路由规则
│   ├── state.json            # 已处理任务记录
│   ├── scripts/
│   │   ├── scheduler.py      # 总调度中心
│   │   └── dashboard.py      # 公司管理后台
│   └── logs/                 # 运营日志
│
├── services/personal-assistant/
│   ├── run_scheduler.sh      # 调度中心启动脚本
│   └── run_dashboard.sh      # 管理后台启动脚本
│
~/Library/LaunchAgents/
├── com.claude.personal-ai-agent.plist      # 调度中心服务
└── com.claude.personal-ai-dashboard.plist  # 管理后台服务
```

---

## 十、运维命令

```bash
# 查看公司运行状态
launchctl list | grep personal-ai

# 重启调度中心
launchctl stop com.claude.personal-ai-agent
launchctl start com.claude.personal-ai-agent

# 重启管理后台
launchctl stop com.claude.personal-ai-dashboard
launchctl start com.claude.personal-ai-dashboard

# 查看运营日志
tail -f ~/.claude/skills/personal-assistant/logs/scheduler.log

# 关闭公司
launchctl unload ~/Library/LaunchAgents/com.claude.personal-ai-agent.plist
launchctl unload ~/Library/LaunchAgents/com.claude.personal-ai-dashboard.plist
```

---

## 十一、扩展公司

### 11.1 成立新部门

编辑 `skills/SKILL.md`，在路由表添加：

```markdown
| 包含 "翻译" | haiku | 翻译部处理 |
```

### 11.2 更换任务系统

不用滴答清单？修改 SKILL.md 中的 Step 2，接入 Todoist / Notion / Things。

### 11.3 添加汇报渠道

除了 Telegram，可以添加：微信、邮件、Slack。

---

## 十二、贡献

欢迎 PR！特别是：
- 支持更多任务系统（Todoist, Notion, Things）
- 支持 Linux / Windows
- 更多汇报渠道
- 新的部门能力

---

## 许可证

MIT License

---

**每个人都可以拥有一家公司，全员 AI，只有老板是人。**

**你负责想，AI 负责做。**
