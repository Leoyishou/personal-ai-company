---
name: bgm-search
description: 搜索免费背景音乐，支持按关键词、情绪、场景搜索，基于 Freesound API。
allowed-tools: Bash(python:*), Read, Write
---

# 背景音乐搜索 (BGM Search)

基于 Freesound API 搜索免费背景音乐，支持按关键词、情绪、场景等条件搜索。

## 快速开始

### 获取 API Key

1. 访问 https://freesound.org/apiv2/apply
2. 注册账号并申请 API credential
3. 获取 Client ID 和 API Key

### 环境配置

在项目根目录 `.env` 文件中添加：

```bash
FREESOUND_API_KEY=your_api_key
```

### 基础使用

```bash
cd .claude/skills/bgm-search
python scripts/search.py "happy upbeat"
```

### 按场景搜索

```bash
# 搜索欢快背景音乐
python scripts/search.py "cheerful background" --duration 60-180

# 搜索科技感音乐
python scripts/search.py "technology electronic" --tag music

# 搜索轻松氛围音乐
python scripts/search.py "relaxing ambient" --limit 5
```

### 下载音乐

```bash
# 搜索并下载第一个结果
python scripts/search.py "cinematic epic" --download --output ./bgm/

# 下载指定 ID 的音乐
python scripts/download.py 12345 --output ./bgm/epic.mp3
```

## 工作流建议

当用户需要背景音乐时，遵循以下流程：

### Step 1: 理解需求

与用户确认：
- 视频/内容的主题和氛围
- 期望的音乐风格（欢快、悲伤、紧张、轻松等）
- 音乐时长要求
- 是否需要循环播放

### Step 2: 构建搜索词

根据需求转换为英文搜索关键词：
- 欢快 → happy, cheerful, upbeat
- 悲伤 → sad, melancholy, emotional
- 紧张 → tense, suspense, dramatic
- 轻松 → relaxing, calm, peaceful
- 科技 → technology, electronic, digital
- 史诗 → epic, cinematic, orchestral

### Step 3: 执行搜索

```bash
python scripts/search.py "关键词" --tag music --duration 60-300 --limit 10
```

### Step 4: 返回结果

将搜索结果返回给用户，包括：
- 音乐名称和预览链接
- 时长和格式信息
- 许可证类型
- 下载链接

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| query | 搜索关键词（英文） | 必填 |
| --tag | 筛选标签，如 music, ambient | 无 |
| --duration | 时长范围，如 60-180（秒） | 无 |
| --limit | 返回结果数量 | 5 |
| --sort | 排序方式: rating, downloads, duration | rating |
| --download | 下载搜索到的音乐 | false |
| --output | 下载保存目录 | ./downloads |

## 常用搜索词

### 情绪类
| 中文 | 英文关键词 |
|------|-----------|
| 欢快 | happy, cheerful, upbeat, joyful |
| 悲伤 | sad, melancholy, emotional, sorrowful |
| 紧张 | tense, suspense, thriller, dramatic |
| 轻松 | relaxing, calm, peaceful, chill |
| 浪漫 | romantic, love, gentle, tender |
| 激励 | inspiring, motivational, uplifting |

### 风格类
| 中文 | 英文关键词 |
|------|-----------|
| 科技 | technology, electronic, digital, futuristic |
| 史诗 | epic, cinematic, orchestral, dramatic |
| 爵士 | jazz, smooth, swing |
| 古典 | classical, piano, orchestra |
| 摇滚 | rock, guitar, energetic |
| 氛围 | ambient, atmospheric, soundscape |

### 场景类
| 中文 | 英文关键词 |
|------|-----------|
| 片头 | intro, opening, logo |
| 背景 | background, underscore |
| 游戏 | game, 8bit, retro |
| 自然 | nature, forest, ocean |
| 城市 | urban, city, street |

## 许可证说明

Freesound 上的音频采用 Creative Commons 许可证：
- **CC0**: 公共领域，可自由使用
- **CC BY**: 需署名作者
- **CC BY-NC**: 需署名，仅限非商业用途

使用时请注意查看具体许可证要求。

## 依赖安装

```bash
cd .claude/skills/bgm-search
pip install -r scripts/requirements.txt
```

## 在 Claude Code 中使用

直接说：

```
帮我找一段欢快的背景音乐
搜索适合科技视频的背景音乐
找一段 2 分钟左右的轻松氛围音乐
```

Claude 会自动调用该 skill 搜索并返回结果。

## API 文档

- Freesound API: https://freesound.org/docs/api/
- 申请 API Key: https://freesound.org/apiv2/apply
