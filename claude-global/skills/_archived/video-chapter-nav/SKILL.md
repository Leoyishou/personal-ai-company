---
name: video-chapter-nav
description: 为视频自动添加动态章节导航条。使用 ASR 转录音频，LLM 分析内容生成章节，生成 .ass 字幕并烧录到视频中。支持火山引擎 ASR 和 Whisper。
allowed-tools: Bash(python:*), Bash(ffmpeg:*), Bash(ffprobe:*), Read, Write
---

# 视频章节导航条生成器

自动为视频添加动态章节导航条，让观众一目了然当前进度。

## 一键生成

```bash
# 最简用法 - 自动生成 4 个章节
python ~/.claude/skills/video-chapter-nav/scripts/chapter_nav.py video.mp4

# 指定章节数量
python ~/.claude/skills/video-chapter-nav/scripts/chapter_nav.py video.mp4 --chapters 5

# 指定输出路径
python ~/.claude/skills/video-chapter-nav/scripts/chapter_nav.py video.mp4 --output video_with_nav.mp4
```

## 工作流程

```
视频输入 → 音频提取 → ASR 转录 → LLM 章节分析 → .ass 字幕 → 视频合成
```

1. **音频提取**: FFmpeg 提取 16kHz 单声道 WAV
2. **语音转文字**: 火山引擎 ASR 或 Whisper (自动选择)
3. **章节分析**: OpenRouter (Gemini) 分析内容，生成章节标题和时间点
4. **字幕生成**: 生成带动态高亮的 .ass 特效字幕
5. **视频合成**: FFmpeg 将字幕烧录到视频

## 核心参数

| 参数 | 说明 | 默认 |
|------|------|------|
| `video` | 输入视频路径 | 必填 |
| `-o, --output` | 输出视频路径 | 自动生成 |
| `-n, --chapters` | 章节数量 | 4 |
| `--asr` | ASR 引擎 (auto/whisper/volcengine) | auto |
| `--position` | 导航条位置 (bottom/top) | bottom |
| `--dry-run` | 试运行，不执行 | - |

## 环境配置

### 必需

```bash
# OpenRouter API Key (用于 LLM 章节分析)
export OPENROUTER_API_KEY="sk-or-v1-xxx"
```

### 可选 - 火山引擎 ASR

如果配置了火山引擎，优先使用（更快更准）：

```bash
# 在火山引擎控制台获取
export VOLC_ASR_APPID="your_app_id"
export VOLC_ASR_TOKEN="your_access_token"
```

获取方式：[火山引擎控制台](https://console.volcengine.com/speech/service/asr) → 创建应用 → 获取 APP ID 和 Access Token

### 未配置火山引擎

自动使用 Whisper (需要安装 openai-whisper)：

```bash
pip install openai-whisper
```

## 导航条效果

导航条显示在视频底部（或顶部），格式如：

```
01 环境配置  ·  02 代码演示  ·  03 功能测试  ·  04 总结
    ↑
  (当前高亮白色，其他灰色)
```

随着视频播放，高亮会自动切换到当前章节。

## 使用示例

### 在 Claude Code 中

```
帮我给这个视频加上章节导航条：~/Videos/tutorial.mp4

给 demo.mp4 添加 5 个章节的导航条
```

### 命令行

```bash
# 基础用法
python ~/.claude/skills/video-chapter-nav/scripts/chapter_nav.py tutorial.mp4

# 5 个章节，导航条在顶部
python ~/.claude/skills/video-chapter-nav/scripts/chapter_nav.py tutorial.mp4 \
  --chapters 5 \
  --position top

# 强制使用 Whisper
python ~/.claude/skills/video-chapter-nav/scripts/chapter_nav.py tutorial.mp4 \
  --asr whisper

# 试运行
python ~/.claude/skills/video-chapter-nav/scripts/chapter_nav.py tutorial.mp4 --dry-run
```

## 输出

默认输出文件名为 `{原文件名}_with_chapters.mp4`，与原视频同目录。

## 依赖

- **FFmpeg**: 音频提取、视频合成 (`brew install ffmpeg`)
- **Python 3.10+**
- **requests**: HTTP 请求
- **openai-whisper** (可选): 本地语音识别

安装依赖：

```bash
cd ~/.claude/skills/video-chapter-nav
pip install -r scripts/requirements.txt
```

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| FFmpeg 未找到 | `brew install ffmpeg` |
| ASR 失败 | 检查网络；使用 `--asr whisper` |
| LLM 失败 | 检查 OPENROUTER_API_KEY |
| 字幕不显示 | 检查视频编码是否兼容 |
| 中文乱码 | 确保系统有 PingFang 字体 |

## 技术说明

### ASS 字幕格式

使用 ASS (Advanced SubStation Alpha) 格式实现动态高亮：
- 定义 Active/Inactive 两种样式
- 每个时间段生成一行字幕事件
- 使用 `{\rStyle}` 语法切换样式

### 为什么不用 PNG 图片叠加？

.ass 字幕方案的优势：
- 渲染速度快（FFmpeg 原生支持）
- 不需要生成中间文件
- 文件体积小
- 更容易调整样式

## 相关文件

- 主脚本: `~/.claude/skills/video-chapter-nav/scripts/chapter_nav.py`
- 依赖: `~/.claude/skills/video-chapter-nav/scripts/requirements.txt`
