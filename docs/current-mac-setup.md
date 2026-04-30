# 当前 Mac 设置

这是当前 Mac 的公开安全版盘点。它记录路径、架构和能力，不记录任何 secret 值。

快照日期：2026-04-30。

## Runtime 层

| 项目 | 当前状态 |
|---|---|
| 主 runtime | Codex |
| CLI binary | `/opt/homebrew/bin/codex` |
| App-bundled binary | `/Applications/Codex.app/Contents/Resources/codex` |
| CLI 版本 | `codex-cli 0.125.0` |
| Codex App bundle | `26.422.71525` |
| Claude Code | 单独安装；仓库里的 `claude-global/` 是旧快照 |
| 主配置 | `/Users/bytedance/.codex/config.toml` |
| Secrets 文件 | `/Users/bytedance/.codex/secret.env` |

Runtime config 里包含模型、trusted project roots、插件配置、MCP servers、memory 开关和 shell environment。所有 token-like 值都不进入仓库。

## 插件和 App 能力

| 能力 | 来源 | 用途 |
|---|---|---|
| Browser Use | Codex plugin | 检查 localhost、浏览网站、测试 dashboard、截图 |
| Computer Use | Codex plugin | 操作没有 API 的 macOS 桌面应用 |
| GitHub | Codex plugin | 读取仓库、issue、PR 和 repo 元数据 |
| Linear | Codex plugin | 项目管理和 issue workflow |
| Documents | Codex primary runtime plugin | 处理 `.docx` |
| Spreadsheets | Codex primary runtime plugin | 处理 `.xlsx`、`.csv`、`.tsv` |
| Presentations | Codex primary runtime plugin | 处理 slide deck |
| Appium MCP | 本地 MCP server | 手机自动化桥接 |
| Blender MCP | 本地 MCP server | 3D / Blender 自动化 |
| Dida365 MCP | 远程 MCP server | 任务和习惯集成 |

## 工作区拓扑

| 工作区 | 职责 | Workspace Skill 数量 |
|---|---|---:|
| `/Users/bytedance/Documents/product-bu` | 产品开发、产品基建、云资源 | 111 |
| `/Users/bytedance/Documents/job-bu` | 数据分析、飞书/Lark、客服知识库 | 32 |
| `/Users/bytedance/Documents/info-bu` | 调研、抓取、内容/媒体生产 | 12 |
| `/Users/bytedance/Documents/invest-bu` | Futu/OpenD 和投资 workflow | 2 |
| `/Users/bytedance/Documents/learning-bu` | 学习实验 | 2 |
| `/Users/bytedance/Documents/Codex` | Codex 会话工作区和实验 | ad hoc |

Workspace 级 skill 约定：

```text
<workspace>/.agents/skills/<skill-name>/SKILL.md
```

这样只有 Agent 在对应业务目录工作时，才会默认看到该业务的能力。

## Skill Roots

| Root | 含义 |
|---|---|
| `/Users/bytedance/.codex/skills` | Codex 用户级 skills |
| `/Users/bytedance/.cc-switch/skills` | 共享兼容 skill root |
| `/Users/bytedance/.agents/skills` | Agent/global 兼容 skill root |
| `<workspace>/.agents/skills` | Workspace-scoped skills |

## Secrets 和 Tokens

| Secret 类型 | 应该放在哪里 | 说明 |
|---|---|---|
| OpenRouter | git 外，由 OpenRouter skills 加载 | 支撑多模型、图像和媒体模型调用 |
| SocialData / TwitterAPI | git 外或私有 workflow config | 支撑推文抓取和 X research |
| Lark/Feishu | git 外 | 支撑 `job-bu` 的 Lark skills |
| 小红书/B站/X cookies | git 外 | 支撑发布和抓取 |
| Futu/OpenD auth | 本地 app/session 状态 | 支撑投资 workflow |
| Supabase keys | git 外 | 新项目优先使用本地 Supabase |

规则：可以写集成方式和路径，不能写凭证值。

## 调度系统

| 调度器 | 当前用途 |
|---|---|
| Codex automation | 每日推文总结、Odyssey 周复盘、暂停状态的播客总结 |
| macOS LaunchAgent | Xiaohongshu MCP、Appium 等本地常驻 daemon |
| `launchcontrol-scheduler` skill | 安装、查看、删除用户级 LaunchAgent |

已观察到的 LaunchAgents：

| Label | 用途 |
|---|---|
| `com.bytedance.xiaohongshu-mcp` | 从 `info-bu` resources 目录常驻运行 Xiaohongshu MCP |
| `com.codex.appium` | 常驻运行 Appium，支撑手机自动化 |

## Browser / Computer / Phone Use

| 能力 | 当前状态 | 为什么重要 |
|---|---|---|
| Browser Use | 已启用；browser state 在 `~/.codex/browser` | 让 Agent 能测试 web 产品和查看本地 dashboard |
| Computer Use | 已通过 Codex plugin 启用 | 让 Agent 能操作没有 CLI/API 的桌面软件 |
| Phone Use | 用户级 `phone-use` skill 已安装 | 让 Agent 在 ask-first 安全边界下操作真机 |
| iPhone bridge | Xcode tooling 能看到一台真实 iPhone；UDID 省略 | 支撑真机测试 |
| Appium | 通过 LaunchAgent 常驻 | 支撑手机 UI 自动化 workflow |

## 需要知道的历史错位

仓库里的旧文件仍然会提到：

| 旧快照 | 当前现实 |
|---|---|
| `/Users/liuyishou/usr/pac` | 当前 BU 根目录在 `/Users/bytedance/Documents/*-bu` |
| `~/.claude` 是唯一全局配置 | 当前主 runtime 配置在 `~/.codex` |
| Claude Code 是唯一 runtime | 当前设计应保持 runtime-neutral，并以 Codex 为主 |

这些旧文件仍然有参考价值，但当前事实以本文档和 skill catalog 为准。
