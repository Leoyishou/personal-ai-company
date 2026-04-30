# Skill Catalog

这是当前 Mac 的 skill 设计盘点，已去除凭证和值。具体 skill 文件会随时间变化；真正重要的是 shared skills 和 BU-scoped skills 的分层。

快照日期：2026-04-30。

## Skill Root 总览

| 作用域 | Root | 观察到的数量 | 用途 |
|---|---|---:|---|
| 用户级 shared | `~/.codex/skills`、`~/.cc-switch/skills`、`~/.agents/skills` | 49 个唯一 shared skills | 跨 BU 通用能力 |
| Product BU | `/Users/bytedance/Documents/product-bu/.agents/skills` | 111 | 产品、云资源、发布、工程 workflow |
| Job/Data BU | `/Users/bytedance/Documents/job-bu/.agents/skills` | 32 | 数据分析、飞书/Lark、知识库处理 |
| Info BU | `/Users/bytedance/Documents/info-bu/.agents/skills` | 12 | 调研、内容、抓取、媒体 |
| Invest BU | `/Users/bytedance/Documents/invest-bu/.agents/skills` | 2 | Futu/OpenD |
| Learning BU | `/Users/bytedance/Documents/learning-bu/.agents/skills` | 2 | 学习实验 |

## 用户级 Shared Skills

| 类别 | Skills |
|---|---|
| 模型/API | `api-openrouter`、`my-ai-api-openrouter`、`api-fetch`、`api-oss`、`api-notify` |
| 媒体 | `api-draw`、`api-asr`、`api-tts`、`api-pdf2markdown`、`volcengine-tts`、`stickman-video`、`xhs-layout`、`xhs-note` |
| 调研 | `research`、`playwright-cli`、`playwright-skill`、`browse-use`、`concept-tree`、`find-topic`、`KOL-info-collect` |
| 产品/开发 | `deploy`、`api-deploy-static`、`api-deploy-testflight`、`chat-to-supabase`、`install-package`、`projects` |
| 数据/投资 | `futu-trades`、`trade-review`、`lakehouse` |
| 自动化/设备 | `phone-use`、`use-my-phone`、`定时任务`、`dida-auto-worker`、`call-claudecode`、`chronicle`、`yao-bayesian-skill` |
| 社媒/内容 | `social-media`、`video`、`xiaoyuzhou-podcast` |
| 归档/参考 | `_archived_api-webfetch`、`_archived_pain-point-research`、`_archived_perplexity-research`、`_archived_research-by-reddit`、`_archived_social-media-download`、`_archived_social-media-publish`、`_archived_video-chapter-nav`、`_archived_调研分析` |

## Workspace Skills By BU

### Product BU

Product BU 的 skill 面最大，它同时承载产品工程工作流和大量 Alibaba Cloud skills。

| 分组 | Skills |
|---|---|
| 工程工作流 | `brainstorming`、`writing-plans`、`executing-plans`、`test-driven-development`、`systematic-debugging`、`verification-before-completion`、`receiving-code-review`、`requesting-code-review`、`subagent-driven-development`、`dispatching-parallel-agents`、`using-git-worktrees`、`finishing-a-development-branch`、`using-superpowers`、`writing-skills` |
| 发布/构建 | `setup-fastlane`、`release`、`snapshot`、`beta`、`api-deploy-obsidian`、`office-hours` |
| 云厂商 | 90+ `alibabacloud-*` skills，覆盖 ECS、OSS、DataWorks、PAI、RDS、SLS、WAF、安全、视频、搜索等云资源操作 |

### Job/Data BU

| 分组 | Skills |
|---|---|
| 数据分析 | `job-data-analysis`、`excel-batch-labeler`、`session-batch-labeler`、`product-level3-labeling`、`product-lifecycle-review` |
| 知识库 | `kefu-fetch`、`douxiaolai-schema`、`laike-ios-agent` |
| 飞书/Lark | `lark-shared`、`lark-doc`、`lark-drive`、`lark-sheets`、`lark-base`、`lark-wiki`、`lark-im`、`lark-mail`、`lark-calendar`、`lark-task`、`lark-contact`、`lark-minutes`、`lark-vc`、`lark-whiteboard`、`lark-whiteboard-screenshot-flow`、`lark-approval`、`lark-attendance`、`lark-okr`、`lark-openapi-explorer`、`lark-skill-maker`、`lark-slides`、`lark-event`、`lark-workflow-meeting-summary`、`lark-workflow-standup-report` |

### Info BU

| 分组 | Skills |
|---|---|
| 调研/抓取 | `apify-research`、`crawl-hub`、`thinking-skill` |
| 媒体生成 | `api-draw`、`api-asr`、`api-tts`、`digital-human`、`seedance-video`、`video-creator`、`remotion-best-practices`、`bgm-search` |
| 发布 | `publish` |

### Invest BU

| 分组 | Skills |
|---|---|
| Futu/OpenD | `futuapi`、`install-futu-opend` |

### Learning BU

| 分组 | Skills |
|---|---|
| 云 notebook / 视频学习 | `alibabacloud-pai-dsw-manage`、`notebooklm-video` |

## 为什么不只是 Skill 名单

| 只有 Skill 名单 | Agent OS 设计 |
|---|---|
| 只能说明有哪些工具 | 还要说明谁在什么上下文里能用这些工具 |
| 很容易变成工具杂物间 | BU 作用域能减少误用和权限扩散 |
| 不能解释工作如何持续 | 定时任务、memory、Linear/GitHub、本地数据库形成闭环 |
| 不能操作真实世界 | Browser Use、Computer Use、Phone Use、Appium、本地 app 把 Agent 接到真实机器上 |

实用规则：全局 skills 应该尽量通用、低风险；带凭证、高风险、强领域的 skills 应该放到拥有它的 workspace 里。
