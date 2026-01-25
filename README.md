# Personal AI Scheduler

**让 AI 成为你 24/7 在线的私人助理**

一个基于 Claude Code 的个人自动化调度系统。它会定时扫描你的待办清单，自动执行可以自动化的任务，并通过 Telegram 向你汇报。

```
你睡觉时，AI 在帮你发推文
你开会时，AI 在帮你下载视频
你度假时，AI 在帮你做调研

你只需要把想法丢进待办清单，剩下的交给 AI。
```

---

## 为什么需要这个？

### 计算机 vs 人类：不对称的优势

人类擅长**创意和决策**，但我们：
- 会累、会忘、会拖延
- 一次只能做一件事
- 睡觉时什么都干不了

计算机（AI）擅长**执行和重复**：
- 7×24 小时不间断
- 可以并行处理多个任务
- 永远不会忘记、不会拖延

**Personal AI Scheduler 的核心理念：**

> 把"想法"和"执行"分离。你负责产生想法，AI 负责执行。

你只需要在待办清单里写下想做的事（哪怕只是一个模糊的念头），AI 会：
1. 每 30 分钟检查一次
2. 判断哪些任务可以自动完成
3. 自动执行并把结果写回来
4. 通过 Telegram 通知你

### 真实使用场景

```
你的输入（滴答清单）              AI 的输出（自动完成）
─────────────────────────────────────────────────────────
发推：今天学到了 3 个技巧...  →   推文已发布 ✅
下载 https://youtube.com/...  →   视频已保存到 ~/Downloads ✅
调研一下 React 19 新特性      →   调研报告已生成 ✅
```

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Personal AI Scheduler                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  【定时扫描器】每 30 分钟自动运行                                  │
│  ├─ 读取滴答清单（或其他待办工具）                                │
│  ├─ AI 判断哪些任务可自动执行                                    │
│  ├─ 根据任务类型选择最优执行方式                                  │
│  │   ├─ 发推文 → x-post skill (haiku, 省钱)                     │
│  │   ├─ 发小红书 → xiaohongshu skill                            │
│  │   ├─ 下载视频 → video-downloader skill                       │
│  │   ├─ 调研分析 → opus (深度思考)                              │
│  │   └─ 其他 → sonnet (通用)                                    │
│  ├─ 执行任务，结果写回待办清单                                    │
│  └─ Telegram 通知你执行结果                                      │
│                                                                  │
│  【Telegram 监听器】实时响应                                      │
│  ├─ 你发消息 → AI 立即执行                                       │
│  └─ 执行完成 → 回复结果                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 前置要求

- macOS（使用 launchd 做定时任务）
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) 已安装并登录
- Python 3.8+
- Telegram 账号（用于通知）

### Step 1: 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/personal-ai-scheduler.git
cd personal-ai-scheduler
```

### Step 2: 复制配置文件

```bash
cp .env.example .env
```

### Step 3: 填写配置

编辑 `.env` 文件，填入你的凭证：

```bash
# 编辑配置
nano .env
# 或
code .env
```

详细的配置说明见下方 [配置指南](#配置指南)。

### Step 4: 运行安装脚本

```bash
./install.sh
```

这个脚本会：
1. 创建必要的目录
2. 安装 Python 依赖
3. 复制文件到正确位置
4. 注册 launchd 服务
5. 发送测试通知到 Telegram

### Step 5: 验证安装

```bash
# 查看服务状态
launchctl list | grep personal-ai

# 手动触发一次
claude -p "/personal-assistant" --dangerously-skip-permissions

# 查看日志
tail -f ~/.claude/skills/personal-assistant/logs/telegram_listener.log
```

---

## 配置指南

### 必填配置

#### 1. 滴答清单 (Dida365/TickTick)

滴答清单是一个待办事项应用，支持 API 访问。

**获取方式：**
1. 访问 [滴答清单开发者平台](https://developer.dida365.com/)
2. 创建应用，获取 Client ID 和 Client Secret
3. 完成 OAuth 授权流程

```env
# .env
DIDA365_CLIENT_ID=your_client_id_here
DIDA365_CLIENT_SECRET=your_client_secret_here
```

> **不用滴答清单？** 你可以修改 SKILL.md，接入其他待办工具（Todoist、Notion 等）。

#### 2. Telegram

用于接收 AI 的通知和主动发消息触发 AI。

**获取方式：**
1. 访问 [Telegram API 开发者页面](https://my.telegram.org/apps)
2. 登录你的 Telegram 账号
3. 创建应用，获取 API ID 和 API Hash

```env
# .env
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=+86your_phone_number
```

**首次登录：**
```bash
python3 scripts/telegram_login.py
# 输入收到的验证码完成登录
# Session 会保存下来，之后不用再登录
```

### 可选配置（扩展功能）

#### 发推文 (X/Twitter)

```env
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret
```

**获取方式：**
1. 访问 [Twitter Developer Portal](https://developer.twitter.com/)
2. 创建项目和应用
3. 生成 Access Token

#### 发小红书

```env
# 小红书使用 Cookie 登录，需要手动获取
# 1. 浏览器登录小红书
# 2. F12 打开开发者工具 → Network → 任意请求 → Headers → Cookie
# 3. 复制完整 Cookie 值
XHS_COOKIE=your_cookie_here
```

#### AI 模型 (OpenRouter)

用于 AI 分析和图片生成：

```env
OPENROUTER_API_KEY=sk-or-v1-your_key_here
```

**获取方式：**
1. 访问 [OpenRouter](https://openrouter.ai/)
2. 注册并创建 API Key

---

## 目录结构

```
~/.claude/
├── skills/
│   └── personal-assistant/
│       ├── SKILL.md              # 调度器核心逻辑
│       ├── state.json            # 已处理任务记录
│       ├── scripts/
│       │   ├── send_telegram.py  # 发送通知
│       │   └── telegram_listener.py  # 监听消息
│       ├── results/              # 执行结果存档
│       └── logs/                 # 日志文件
│
├── services/
│   └── personal-assistant/
│       ├── run.sh                # 定时任务启动脚本
│       └── run_listener.sh       # 监听器启动脚本
│
~/Library/LaunchAgents/
├── com.claude.personal-assistant.plist   # 定时扫描服务
└── com.claude.telegram-listener.plist    # Telegram 监听服务
```

---

## 使用方式

### 方式 1：被动等待（定时扫描）

把任务写进滴答清单，等 AI 自动执行：

```
任务标题：发推：今天学到的 3 个 Claude Code 技巧
任务描述：
1. 可以用 /personal-assistant 自动处理任务
2. MCP 可以让 AI 调用滴答清单
3. launchd 可以定时运行 Claude
```

30 分钟内，你会收到 Telegram 通知：
```
老板，我已经帮你做完了：
✅ 发推：今天学到的 3 个 Claude Code 技巧 → https://x.com/...
```

### 方式 2：主动触发（Telegram 消息）

打开 Telegram → Saved Messages → 发送：

```
帮我发条推：Claude Code 真好用
```

几秒后收到：
```
[Claude] 执行完成：
推文已发布：https://x.com/...
```

### 任务格式建议

**好的任务格式（AI 能执行）：**
```
发推：具体的推文内容
下载视频：https://youtube.com/watch?v=xxx
调研：React 19 有哪些新特性
生成图片：一只可爱的柴犬在看电脑
```

**不好的任务格式（AI 会跳过）：**
```
发两条  ← 发什么？
洗稿发小红书  ← 洗哪篇？
做个视频  ← 什么主题？
```

---

## 常见问题

### Q: Telegram 登录失败？

确保：
1. API ID 和 Hash 正确
2. 手机号格式正确（+86...）
3. 能收到 Telegram 验证码

手动测试：
```bash
python3 ~/.claude/skills/personal-assistant/scripts/telegram_login.py
```

### Q: 定时任务没运行？

检查 launchd 服务状态：
```bash
launchctl list | grep personal-ai
```

查看日志：
```bash
cat ~/.claude/services/personal-assistant/stdout.log
```

### Q: 滴答清单连接失败？

确保 MCP 配置正确。检查 `~/.claude.json`：
```json
{
  "mcpServers": {
    "dida365": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-dida365"],
      "env": {
        "DIDA365_CLIENT_ID": "your_id",
        "DIDA365_CLIENT_SECRET": "your_secret"
      }
    }
  }
}
```

---

## 扩展开发

### 添加新的执行能力

编辑 `SKILL.md`，在任务路由表中添加：

```markdown
| 包含 "翻译" | general-purpose | haiku | 调用翻译 API |
```

### 接入其他待办工具

修改 Step 2，替换滴答清单 MCP 调用为你的工具：

```markdown
### Step 2: 获取待办任务

调用 `your_tool_api` 获取所有未完成任务。
```

### 添加更多通知渠道

除了 Telegram，你可以添加：
- 微信（通过 Server 酱）
- 邮件
- Slack

---

## 贡献

欢迎提交 PR！特别是：
- 支持更多待办工具（Todoist, Notion, Things 等）
- 支持更多通知渠道
- 支持 Linux / Windows
- 更好的错误处理

---

## 许可证

MIT License

---

## 致谢

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) - Anthropic 的 AI 编程助手
- [滴答清单](https://dida365.com/) - 待办事项管理
- [Telethon](https://github.com/LonamiWebs/Telethon) - Telegram 客户端库

---

**让 AI 成为你的超级助理，把时间留给真正重要的事。**
