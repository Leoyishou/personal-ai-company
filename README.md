# Personal AI Company

> 一个面向个人的 Agent OS：Codex / Claude Code 负责执行，BU 工作区负责隔离上下文和技能，本机基建负责把一次性 prompt 变成可持续运行的系统。

这个仓库不应该被理解成“一堆 prompts”。它真正想表达的是：一个人如何在自己的 Mac 上搭出一家公司形态的 AI 执行系统。

| 层级 | 本质 | 当前形态 |
|---|---|---|
| Agent Runtime | 能推理、读写文件、跑命令、调工具、操作应用的执行外壳 | 当前这台 Mac 以 Codex 为主，Claude Code 可以作为并存 runtime |
| BU 工作区 | 按业务目标隔离上下文、默认规则和可用 skill | `/Users/bytedance/Documents` 下的 `product-bu`、`job-bu`、`info-bu`、`invest-bu`、`learning-bu` |
| Skill Catalog | Agent 可调用的能力模块 | 用户级 shared skills + 各 BU 的 `.agents/skills` |
| 基建层 | 凭证、API、本地服务、定时任务、设备桥接 | OpenRouter、平台 token、Supabase/Redis 方案、LaunchAgent、Browser Use、Computer Use、Phone Use |
| PMO / Memory | 产出追踪、session 复盘、经验沉淀 | GitHub/Linear 插件、Codex memories、automations、历史 hooks/agents |

## 一张表讲清设计思想

| 设计选择 | 为什么需要 | 例子 |
|---|---|---|
| Runtime 可替换 | Codex 和 Claude Code 本质上都是 Agent 执行外壳，不应该把公司设计绑死在某个 UI 上 | 当前 Codex App + CLI 是主力；`claude-global/` 保留为历史 Claude Code 快照 |
| Agent 和 Skill 分离 | Agent 的身份、目标和工具箱应该分层；增加能力不等于重写人格 prompt | `api-openrouter`、`api-draw`、`futu-trades`、`lark-doc`、`phone-use` |
| 按 BU 隔离工作区 | 产品、数据分析、内容调研、投资的风险和默认工具完全不同 | `Documents/product-bu/.agents/skills`、`Documents/job-bu/.agents/skills` |
| 基建是一等公民 | token、定时任务、设备连接、浏览器状态，决定 Agent 能不能真正做事 | `~/.codex/secret.env`、LaunchAgents、Appium、Futu OpenD、Browser Use sessions |
| PMO 是管理闭环 | 系统应该知道 Agent 做过什么，并把后续工作路由到正确位置 | session 摘要、GitHub/Linear 集成、周复盘、每日推文总结 |

## 当前 Mac 快照

这个 README 已经从旧的 `/Users/liuyishou/usr/pac` 叙事，重构为当前这台 Mac 的真实结构。

| 项目 | 当前证据 |
|---|---|
| Codex CLI | `/opt/homebrew/bin/codex`，版本 `codex-cli 0.125.0` |
| Codex App | `/Applications/Codex.app`，bundle `26.422.71525` |
| 已启用插件 | Browser Use、Computer Use、GitHub、Linear、Documents、Spreadsheets、Presentations |
| MCP 桥接 | Appium、Blender MCP、Dida365 |
| 用户级 skill 根目录 | `~/.codex/skills`、`~/.cc-switch/skills`、`~/.agents/skills` |
| 工作区级 skills | `Documents/product-bu`、`Documents/job-bu`、`Documents/info-bu`、`Documents/invest-bu`、`Documents/learning-bu` |
| 定时系统 | Codex automations + macOS LaunchAgents |
| 设备控制 | Xcode 能看到真实 iPhone；Appium 作为 LaunchAgent 常驻 |
| 凭证策略 | 只记录路径，不提交值；主要在 `~/.codex/secret.env` 和 runtime config 中 |

更多细节见：[当前 Mac 设置](docs/current-mac-setup.md)。

## BU 工作区模型

| BU | 本机路径 | 职责 | Skill 形态 |
|---|---|---|---|
| Product BU | `/Users/bytedance/Documents/product-bu` | 产品开发、发布、云资源和工程工作流 | 111 个 workspace skills，包括 Alibaba Cloud、Superpowers 工作流、Fastlane、release/snapshot |
| Job/Data BU | `/Users/bytedance/Documents/job-bu` | 数据分析、飞书/Lark、知识库处理 | 32 个 workspace skills，包括 Lark API、Excel 批处理、客服知识库工具 |
| Info BU | `/Users/bytedance/Documents/info-bu` | 调研、内容生产、媒体管线、抓取 | 12 个 workspace skills，包括 ASR/TTS、视频、生图、Apify/crawl、发布 |
| Invest BU | `/Users/bytedance/Documents/invest-bu` | 交易数据、富途 OpenD、投资复盘 | 2 个 workspace skills：Futu API 和 OpenD 安装 |
| Learning BU | `/Users/bytedance/Documents/learning-bu` | 学习实验、云端 notebook | 2 个 workspace skills |
| Codex Sessions | `/Users/bytedance/Documents/Codex` | Codex 会话工作区、实验、repo checkout | 按日期和主题生成临时/项目目录 |

关键思想：**不要把所有工具都给所有 Agent**。高风险、强领域、带凭证的 skill 应该放在拥有它的 BU 工作区里。

## Skill Catalog

这个仓库真正对别人有启发的部分，是 skill 地图：有哪些能力、放在哪里、为什么这么隔离。

| 范围 | 数量 | 例子 |
|---|---:|---|
| 用户级 shared skills | 49 | `api-openrouter`、`api-draw`、`api-fetch`、`futu-trades`、`phone-use`、`playwright-cli`、`research`、`social-media` |
| Product workspace | 111 | Alibaba Cloud skills、Superpowers 工作流、`setup-fastlane`、`office-hours`、release/snapshot |
| Job/Data workspace | 32 | Lark 套件、Excel/session 批处理、知识库工具 |
| Info workspace | 12 | ASR/TTS、视频、生图、抓取、发布 |
| Invest workspace | 2 | `futuapi`、`install-futu-opend` |
| Learning workspace | 2 | 云 notebook / 视频学习相关 skills |

完整清单见：[Skill Catalog](docs/skill-catalog.md)。

## 必须强调的基建

| 基建 | 为什么重要 | 公开仓库里怎么表达 |
|---|---|---|
| OpenRouter token | 让 skill 能统一调用多模型、图像和媒体模型 | 只写“由 OpenRouter skills 加载”，不写 token 值 |
| 平台 token / cookies | 让 Agent 从“写文案”升级为“能抓取、发布、回填数据” | X/Twitter、小红书、B站、Lark、Futu、Telegram 等都只写集成类型 |
| Browser Use | 让 Agent 能检查 localhost、后台页面、网页应用 | Codex 插件；状态在 `~/.codex/browser` |
| Computer Use | 让 Agent 能操作没有 API 的 macOS UI | Codex bundled plugin |
| Phone Use | 让 Agent 能在显式安全边界下测试/操作真机 | `phone-use` skill + Xcode/Appium/iPhone bridge |
| LaunchAgents | 让任务在没有聊天会话时仍然常驻 | Xiaohongshu MCP 和 Appium 已用用户级 LaunchAgent |
| Codex automations | Agent 原生定时任务 | 每日推文总结、Odyssey 周复盘等 |
| 本地数据库/队列 | 给 Agent 持久化状态和任务队列 | Supabase/Redis 仍然是架构组件 |

## 仓库地图

| 路径 | 状态 | 用途 |
|---|---|---|
| `README.md` | 当前入口 | 架构总览和对外说明 |
| `docs/current-mac-setup.md` | 当前 | 这台 Mac 的 runtime、插件、基建、设备能力盘点 |
| `docs/skill-catalog.md` | 当前 | 按作用域和 BU 整理的 skill 地图 |
| `claude-global/` | 历史快照 | 旧 Claude Code 全局配置、skills、hooks、agents 和实验 |
| `pmo/` | 历史 + 可复用 | PMO session 追踪设计和 hook 示例 |
| `product-bu/`、`content-bu/`、`research-bu/`、`investment-bu/` | 历史示例 | 旧 `~/usr/pac` 模型下的 BU 目录 |
| `infrastructure/` | 可复用模式 | Supabase schema 和本地基建说明 |

## 如何复制这个模式

1. 先选 Agent Runtime：Codex、Claude Code，或两者并存。
2. 先建 BU 工作区，再写 skills。
3. 从第一天开始把 credentials 和 cookies 放在 git 外。
4. 通用、安全的 skills 放用户级；高风险、强领域的 skills 放 workspace `.agents/skills`。
5. 至少加一层调度：Agent 任务用 Codex automations，OS daemon 用 LaunchAgents。
6. 文本/文件工作流稳定后，再接 Browser Use、Computer Use、Phone Use。
7. 最后加 PMO/memory：等系统真的在产出，再自动追踪和复盘。

## 安全规则

这个仓库永远不应该包含真实 token、cookies、账号密钥、session 数据库或手机 UDID。可以记录路径和架构，不记录秘密值。

MIT License
