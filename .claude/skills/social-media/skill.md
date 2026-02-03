---
name: social-media
shortname: social-media
description: 社交媒体统一入口 - 下载/发布/文案。支持小红书、X/Twitter、抖音、B站、YouTube。自动识别平台和动作。
version: 1.0.0
author: Claude
allowed-tools: Bash(python:*), Read, Write, Glob, WebFetch
model: sonnet
tags: [social-media, xiaohongshu, twitter, douyin, bilibili, youtube, download, publish]
---

# Social Media - 社交媒体统一入口

## 架构概览

本 skill 采用**双策略模式**，自动识别平台和动作：

```
┌─────────────────────────────────────────────────────────────┐
│                   social-media skill                         │
├─────────────────────────────────────────────────────────────┤
│  PlatformStrategy（平台策略）  │  ActionStrategy（动作策略）  │
│  - 小红书 (xiaohongshu)       │  - download（下载内容）      │
│  - X/Twitter (twitter)        │  - publish（发布内容）       │
│  - 抖音 (douyin)              │  - copywriting（写文案）     │
│  - B站 (bilibili)             │  - repurpose（内容分发）     │
│  - YouTube (youtube)          │                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 一、策略调度规则

### 1.1 平台自动识别

| URL 特征 | 平台 |
|---------|------|
| `xhslink.com`, `xiaohongshu.com` | 小红书 |
| `x.com`, `twitter.com` | X/Twitter |
| `v.douyin.com`, `douyin.com` | 抖音 |
| `bilibili.com`, `b23.tv` | B站 |
| `youtube.com`, `youtu.be` | YouTube |

### 1.2 动作自动识别

| 用户输入 | 动作 | 说明 |
|---------|------|------|
| "下载这个 [链接]" | `download` | 下载视频/图片/元数据 |
| "保存这个 [链接]" | `download` | 同上 |
| "发到 X/小红书/B站" | `publish` | 发布内容 |
| "帮我写个文案" | `copywriting` | 生成文案 |
| "把这个内容发到多个平台" | `repurpose` | 多平台分发 |

### 1.3 组合示例

| 用户输入 | Platform | Action |
|---------|----------|--------|
| "下载这个抖音" | douyin | download |
| "发到 X 和小红书" | [twitter, xiaohongshu] | publish |
| "帮我写个小红书文案" | xiaohongshu | copywriting |
| "把这个视频发到 B 站" | bilibili | publish |

---

## 二、下载动作（Action: download）

### 2.1 统一命令

```bash
python3 ~/.claude/skills/social-media/scripts/platforms/social_download.py <command> <args>
```

### 2.2 自动识别平台

```bash
# 解析链接（自动识别平台）
python3 ~/.claude/skills/social-media/scripts/platforms/social_download.py parse "<URL>" --json

# 下载内容（自动识别平台）
python3 ~/.claude/skills/social-media/scripts/platforms/social_download.py download "<URL>" -o ~/Downloads
```

### 2.3 平台专用命令

**X/Twitter：**
```bash
python3 ~/.claude/skills/social-media/scripts/platforms/social_download.py twitter <TWEET_ID> -o ~/Downloads
```

**小红书：**
```bash
python3 ~/.claude/skills/social-media/scripts/platforms/social_download.py xiaohongshu "<URL>" -o ~/Downloads
```

**抖音：**
```bash
python3 ~/.claude/skills/social-media/scripts/platforms/social_download.py douyin "<URL或分享文本>" -o ~/Downloads
```

### 2.4 输出格式

```
~/Downloads/
├── username_video.mp4      # 视频
├── image_001.jpg           # 图片
├── metadata.json           # 元数据（含评论）
└── summary.md              # 可读摘要
```

### 2.5 平台能力对照

| 平台 | 视频 | 图片 | 评论 | 元数据 |
|------|:----:|:----:|:----:|:------:|
| 小红书 | ✅ | ✅ | ✅ (MCP) | ✅ |
| X/Twitter | ✅ | ✅ | ✅ | ✅ |
| 抖音 | ✅ | - | - | - |
| B站 | ✅ | - | - | - |
| YouTube | ✅ | - | - | - |

---

## 三、发布动作（Action: publish）

### 3.1 平台发布命令

**X/Twitter：**
```bash
python3 ~/.claude/skills/x-post/scripts/x_post.py "推文内容" [-i 图片路径]
```

**小红书（图文）：**
```bash
python3 ~/.claude/skills/xiaohongshu/scripts/xhs_publish.py publish \
  --title "标题" \
  --content "正文" \
  --tags "标签1,标签2" \
  --images "图片路径"
```

**小红书（视频）：**
```bash
python3 ~/.claude/skills/xiaohongshu/scripts/xhs_publish.py video \
  --title "标题" \
  --content "正文" \
  --tags "标签1,标签2" \
  --video "视频路径"
```

**B站：**
```bash
cd ~/.claude/skills/biliup-publish && biliup upload "视频路径" \
  --title "标题" \
  --desc "简介" \
  --tag "标签1,标签2" \
  --tid 231
```

### 3.2 登录检查（发布前必须）

```bash
# X - 无需检查，API 已配置

# 小红书
python3 ~/.claude/skills/xiaohongshu/scripts/xhs_publish.py check

# B站
ls ~/.claude/skills/biliup-publish/cookies.json
```

### 3.3 平台限制

| 平台 | 文字限制 | 图片 | 视频 | 登录方式 |
|------|---------|:----:|:----:|---------|
| X | 280字符 | 4张 | - | API密钥 |
| 小红书 | 标题20字，正文1000字 | ✅ | ✅ | 扫码 |
| B站 | 标题80字 | 封面 | ✅ | 扫码 |

### 3.4 账号信息

| 平台 | 账号 |
|------|------|
| X/Twitter | liuysh2 |
| B站 | 转了码的刘公子 |
| 小红书 | (扫码登录) |

---

## 四、文案动作（Action: copywriting）

### 4.1 风格规范

**禁止使用：**
- 数字圆圈 emoji：1️⃣ 2️⃣ 3️⃣
- 过度 emoji 堆砌
- 营销号腔调

**推荐格式：**
- 列表序号：1. 2. 3. 或 一、二、三
- 强调：「直角引号」包裹关键词
- 语气：简洁直接，有观点

### 4.2 平台适配

| 平台 | 标题 | 正文 | 标签 |
|------|------|------|------|
| 小红书 | ≤20字 | ≤1000字 | 数组格式，不带# |
| X | - | ≤280字符 | 可用# |
| B站 | ≤80字 | 无限制 | 逗号分隔 |

### 4.3 标题公式

```
数字+结果：「3招搞定xxx」
身份+痛点：「程序员必看！xxx」
反常识：「原来xxx才是关键」
提问式：「为什么xxx？」
```

### 4.4 正文结构

```
钩子（1句话抓注意力）
↓
核心内容（分点阐述）
↓
总结/金句收尾
```

### 4.5 内容IP：「n张图xxx」系列（小红书专属）

**系列定位**：用固定数量的图片讲透一件事，形成账号辨识度

**标题格式**：
```
[n]张图[动词][主题]

动词选择：
- 读懂：知识概念类（读懂RLHF、读懂量化交易）
- 盘点：列表清单类（盘点AI Agent框架、盘点编程语言）
- 了解：人物介绍类（了解Sam Altman、了解黄仁勋）
- 搞定：实操教程类（搞定Git工作流、搞定Docker部署）
- 看透：深度分析类（看透OpenAI商业模式）
```

**图片数量选择**：
| 数量 | 适用场景 | 信息密度 |
|------|---------|---------|
| 3张 | 快速科普、简单概念 | 低，易传播 |
| 5张 | 标准讲解、人物介绍 | 中，平衡 |
| 7-9张 | 深度盘点、完整教程 | 高，需耐心 |

**每张图的内容结构**：
```
第1张：封面（标题+核心视觉）
第2张：引入/背景/为什么重要
第3-n-1张：核心内容（每张一个要点）
第n张：总结/行动号召/关注引导
```

**设计规范**：
- 统一视觉风格（配色、字体、排版）
- 每张图信息量适中，不超过3个核心点
- 使用 `/api-draw` 生成，保持一致性
- 封面突出数字「n」和关键词

**示例**：
```
5张图读懂RLHF
├── 图1: 封面「5张图读懂RLHF」
├── 图2: 什么是RLHF？为什么重要？
├── 图3: 核心流程第一步：SFT
├── 图4: 核心流程第二步：RM训练
├── 图5: 核心流程第三步：PPO优化
└── 图6: 总结+延伸阅读
```

**触发词**：当用户说「做一个n张图」「图文盘点」「图解xxx」时，自动应用此模板

---

## 五、分发动作（Action: repurpose）

### 5.1 工作流程

```
1. 确认内容和目标平台
2. 检查各平台登录状态
3. 内容适配（根据平台限制调整）
4. 依次发布
5. 汇总结果
```

### 5.2 内容适配规则

| 平台 | 文字处理 | 媒体处理 |
|------|----------|----------|
| X | 精简到280字以内 | 最多4张图 |
| 小红书 | 标题≤20字，正文≤1000字 | 图片/视频 |
| B站 | 标题≤80字 | 仅视频 |

### 5.3 结果汇总格式

```
发布结果：
✅ X: https://x.com/i/status/xxx
✅ 小红书: 发布成功
✅ B站: https://www.bilibili.com/video/BVxxx
```

---

## 六、API 凭证配置

### X/Twitter

```bash
# twitterapi.io（推荐）
export TWITTERAPI_IO_KEY="your_key"

# 或官方 API
export X_API_KEY="your_key"
export X_API_SECRET="your_secret"
export X_ACCESS_TOKEN="your_token"
export X_ACCESS_TOKEN_SECRET="your_token_secret"
```

### 小红书

通过 MCP 访问：
```
mcp__xiaohongshu-mcp__check_login_status
```

### 抖音

Cookies 文件：`~/.claude/douyin_cookies.txt`

### B站

Cookies 文件：`~/.claude/skills/biliup-publish/cookies.json`

---

## 七、常用分区 ID（B站）

| tid | 分区 | 适用内容 |
|-----|------|----------|
| 231 | 计算机技术 | 编程、AI、技术教程 |
| 230 | 软件应用 | 软件测评、使用教程 |
| 201 | 科学科普 | 知识科普 |
| 207 | 财经商业 | 商业、投资 |
| 160 | 生活记录 | 日常Vlog |

---

## 八、故障排查

| 问题 | 解决方案 |
|------|---------|
| Twitter 429 | twitterapi.io 配额用尽，等待重置 |
| 小红书 404 | 笔记可能已删除或私密 |
| 抖音页面超时 | 检查网络，增加等待时间 |
| B站上传失败 | 刷新登录：`biliup renew` |
| Playwright 未安装 | `pip install playwright && playwright install chromium` |

---

## 九、依赖安装

```bash
pip install requests requests-oauthlib playwright
playwright install chromium
```

---

## 十、相关 Skill

| Skill | 用途 |
|-------|------|
| `video` | 视频制作（配合发布） |
| `draw` | 封面生成 |
| `research` | 内容调研 |
