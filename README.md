# Personal AI Agent

**让 AI 成为你 24/7 在线的私人助理**

---

## 想象一下

你是字节跳动的张一鸣。

你不需要亲自写代码、做设计、写文案。你只需要**下达指令**：

- 「战投部门，调研一下 AI 视频赛道，下周给我报告」
- 「产品部门，把这个新功能上线，开始赚钱」
- 「公关部门，发一波媒体稿，提升声量」

然后，各个部门就开始运转，结果自动汇报给你。

**现在，AI 可以成为你的这些"部门"。**

```
你睡觉时，AI 在帮你发推文、发小红书
你开会时，AI 在帮你下载视频、整理素材
你度假时，AI 在帮你做行业调研、写分析报告

你只需要把想法丢进待办清单，剩下的交给 AI。
```

---

## 两种工作模式

### 模式一：随时响应

在 Telegram 发消息，AI 立即执行。

```
你：帮我发条推，内容是"Claude Code 真好用"
AI：[Claude] 收到，正在处理...
AI：[Claude] 执行完成：推文已发布 https://x.com/...
```

**适合**：突然想到要做的事，马上让 AI 去做。

### 模式二：自动巡检

每 30 分钟，AI 自动扫描你的待办清单（滴答清单），分析每个任务：

- **能自动完成的** → 直接执行，结果写回待办
- **需要你决策的** → 提供参考信息，等你确认
- **无法执行的** → 告诉你缺少什么信息

```
AI：老板，我已经帮你做完了 2 件事：
    ✅ 发推：今天学到的 3 个技巧 → https://x.com/...
    ✅ 下载视频：xxx.mp4 → ~/Downloads/

    ⏭️ 跳过 1 件（需要更多信息）：
    - "洗稿发小红书"（洗哪篇内容？）
```

**适合**：把想法随手记进待办清单，让 AI 在后台默默处理。

---

## 实现原理：LLM + 图灵机

### 为什么这个组合如此强大？

```
LLM（大语言模型）     +     图灵机（计算机）
       ↓                         ↓
   理解、推理、创作           7×24 不间断执行
       ↓                         ↓
   "知道该做什么"            "能一直做下去"
       ↓                         ↓
       └──────────┬──────────────┘
                  ↓
    任何人都能拥有一支无限规模的智能团队
```

**LLM 的能力**：
- 理解自然语言指令（"帮我发条推"）
- 判断任务是否可执行（"这个描述太模糊"）
- 选择最优执行方式（"这个任务用 haiku 就够了"）
- 生成执行结果（写推文、做调研报告）

**图灵机的能力**：
- 永不疲倦，7×24 小时运行
- 精确执行，不会忘记不会出错
- 并行处理，同时做多件事
- 定时触发，每 30 分钟自动检查

**两者结合**：
- 你负责产生想法
- LLM 负责理解和规划
- 图灵机负责执行和监控
- 结果自动汇报给你

### 这意味着什么？

**智力，正在变成自来水。**

100 年前，电力从奢侈品变成了基础设施。工厂不再需要自建发电机，只需要插上插头。

现在，同样的事情正在发生在"智力"上。

过去，你想完成一个任务，需要：
- 自己学会这个技能，或者
- 花钱雇一个会的人

现在，你只需要**描述你想要什么**，AI 就能帮你完成。

**这不是未来，这是现在。**

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Personal AI Agent                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  统一调度器 (scheduler.py) - 常驻运行                    │    │
│  │  ├─ 监听 Telegram 消息 → 收到立即执行                    │    │
│  │  ├─ 每 30 分钟扫描滴答清单 → 执行可自动化任务             │    │
│  │  └─ 根据任务类型路由到不同模型                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│                            ↓ 拉起子进程                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Claude Code 子进程                                       │    │
│  │  ├─ haiku: 发推、发小红书、下载视频（快速、省钱）         │    │
│  │  ├─ sonnet: 生成图片、通用任务                           │    │
│  │  └─ opus: 深度调研、分析报告                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│                            ↓                                     │
│              执行结果 → Telegram 通知 / 写回待办清单              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 前置要求：搭建你的「公司」

| 你需要准备的 | 相当于张一鸣的... | 作用 |
|-------------|------------------|------|
| **Mac 电脑** | 办公大楼 | AI 助理 7×24 运行的物理载体 |
| **[Amphetamine](https://apps.apple.com/app/amphetamine/id937984704)** | 大楼的电力系统 | 防止 Mac 休眠，确保永不断电（免费） |
| **[Claude Code Max](https://claude.com/download)** | 校招预算 | 雇佣顶级 AI 人才的薪资（$100/月或$200/月） |
| **[Telegram](https://telegram.org/)** | 飞书 | 你和 AI 助理的沟通渠道 |
| **[滴答清单](https://dida365.com/)** | 你脑海里的想法 | AI 定期扫描，自动执行可执行的任务 |
| **[X (Twitter)](https://x.com/)** | 海外公关部 | AI 帮你发推文、做海外声量 |
| **[小红书](https://www.xiaohongshu.com/)** | 国内公关部 | AI 帮你发笔记、做国内声量 |
| **股票账户** | 战投部的仓位 | AI 帮你监控持仓、分析研报（可选） |

> **重要**：Mac 休眠后 launchd 服务会暂停。安装 Amphetamine 并设置「Indefinitely」保持唤醒，确保 AI 助理 24/7 在线。

### Step 1: 克隆项目

```bash
git clone https://github.com/Leoyishou/personal-ai-agent.git
cd personal-ai-agent
```

### Step 2: 复制配置文件

```bash
cp .env.example .env
```

### Step 3: 填写配置

```bash
nano .env
```

详细说明见 [配置指南](#配置指南)。

### Step 4: 运行安装脚本

```bash
./install.sh
```

### Step 5: 验证

```bash
# 查看服务状态
launchctl list | grep personal-ai

# 查看日志
tail -f ~/.claude/skills/personal-assistant/logs/scheduler.log
```

---

## 配置指南

### 必填：Telegram

用于接收通知 + 发消息触发 AI。

**获取方式**：
1. 访问 https://my.telegram.org/apps
2. 登录 → 创建应用
3. 获取 API ID 和 API Hash

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+8613800138000
```

### 必填：滴答清单

用于待办清单自动扫描。

**获取方式**：
1. 访问 https://developer.dida365.com/
2. 创建应用 → 获取凭证

```env
DIDA365_CLIENT_ID=your_client_id
DIDA365_CLIENT_SECRET=your_client_secret
```

> 不用滴答清单？可以修改 SKILL.md 接入其他工具。

### 可选：扩展能力

```env
# 发推文
X_API_KEY=...
X_ACCESS_TOKEN=...

# AI 模型 (OpenRouter)
OPENROUTER_API_KEY=...

# 小红书 (Cookie)
XHS_COOKIE=...
```

---

## 使用示例

### Telegram 直接指令

```
帮我发条推：今天天气真好
下载这个视频 https://youtube.com/watch?v=xxx
调研一下 React 19 新特性
生成一张图：赛博朋克风格的猫
```

### 待办清单任务格式

**好的格式（AI 能执行）**：
```
发推：具体的推文内容
下载视频：https://youtube.com/xxx
调研：React 19 有哪些新特性
```

**不好的格式（AI 会跳过）**：
```
发两条  ← 发什么？
洗稿  ← 洗哪篇？
做视频  ← 什么主题？
```

---

## 目录结构

```
~/.claude/
├── skills/personal-assistant/
│   ├── SKILL.md              # 定时扫描任务判断逻辑
│   ├── state.json            # 已处理任务记录
│   ├── scripts/
│   │   └── scheduler.py      # 统一调度器（核心）
│   └── logs/                 # 日志
│
├── services/personal-assistant/
│   └── run_scheduler.sh      # 调度器启动脚本
│
~/Library/LaunchAgents/
└── com.claude.personal-ai-agent.plist    # launchd 服务配置
```

---

## 管理命令

```bash
# 查看服务状态
launchctl list | grep personal-ai

# 重启服务
launchctl stop com.claude.personal-ai-agent
launchctl start com.claude.personal-ai-agent

# 查看日志
tail -f ~/.claude/skills/personal-assistant/logs/scheduler.log

# 卸载服务
launchctl unload ~/Library/LaunchAgents/com.claude.personal-ai-agent.plist

# 重新加载（修改配置后）
launchctl unload ~/Library/LaunchAgents/com.claude.personal-ai-agent.plist
launchctl load ~/Library/LaunchAgents/com.claude.personal-ai-agent.plist
```

---

## 扩展开发

### 添加新能力

编辑 `skills/SKILL.md`，在任务路由表添加：

```markdown
| 包含 "翻译" | haiku | 调用翻译 API |
```

### 接入其他待办工具

修改 SKILL.md 中的 Step 2，替换滴答清单调用。

### 添加通知渠道

除了 Telegram，可以添加：微信、邮件、Slack。

---

## 贡献

欢迎 PR！特别是：
- 支持更多待办工具（Todoist, Notion, Things）
- 支持 Linux / Windows
- 更多通知渠道

---

## 许可证

MIT License

---

**智力如自来水，AI 如图灵机。打开水龙头，让想法流淌。**
