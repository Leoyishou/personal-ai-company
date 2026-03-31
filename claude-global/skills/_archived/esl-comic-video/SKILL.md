---
name: esl-comic-video
description: 将故事文本(txt/md)和音频转换成漫画风格视频。支持自动语音转录、AI图片生成、字幕烧录等功能。适用于ESL教学视频制作。
allowed-tools: Bash(python:*), Bash(edge-tts:*), Bash(ffmpeg:*), Read, Write
---

# ESL 漫画视频生成器

将英语学习故事转换成白板简笔画风格的教学视频。

## 一键生成

```bash
# 最简用法 - 只需提供故事文本
python ~/.claude/skills/esl-comic-video/scripts/make_video.py --story story.txt

# ESL 学习者推荐 - 0.75 倍速慢放
python ~/.claude/skills/esl-comic-video/scripts/make_video.py --story story.txt --speed 0.75
```

**自动化功能**：
- 自动检测 ElevenLabs API Key（已配置）
- 自动生成高质量 TTS 配音
- 自动生成简笔画图片 + 词汇标注
- 自动烧录字幕
- 自动调整播放速度
- 完成后自动打开视频

## 核心参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--story` | 故事文本文件 | `--story lesson.txt` |
| `--text` | 直接输入文本 | `--text "Hello world..."` |
| `--audio` | 已有音频文件 | `--audio lesson.mp3` |
| `--speed` | 播放速度 | `--speed 0.75` (慢放) |
| `--output` | 输出目录 | `--output ./videos` |
| `--name` | 项目名称 | `--name lesson01` |

## 速度控制

| 速度值 | 效果 | 适用场景 |
|-------|------|---------|
| `0.75` | 慢放 75% | ESL 初学者 |
| `0.85` | 慢放 85% | ESL 中级 |
| `1.0` | 原速（默认）| 正常学习 |
| `1.25` | 加速 125% | 复习回顾 |

## TTS 配置

### 自动模式（推荐）

默认使用 `--tts auto`，自动检测：
- 有 ElevenLabs Key → 使用 ElevenLabs（更自然）
- 无 Key → 使用 Edge TTS（免费）

### 手动指定

```bash
# 强制使用 Edge TTS
python make_video.py --story story.txt --tts edge

# 强制使用 ElevenLabs
python make_video.py --story story.txt --tts elevenlabs
```

### 已配置的 API Keys

位置：`/Users/liuyishou/usr/projects/inbox/ESL-video/.env`

```
ELEVENLABS_API_KEY=sk_xxx
ELEVENLABS_VOICE_ID=kPzsL2i3teMYv0FxEYQ6
```

## 图片风格

**白板简笔画教学风格**：
- 纯白背景 (#FFFFFF)
- 黑色线条画
- 每帧标注 2-3 个关键词汇
- 箭头指向对应物体/动作

## 功能开关

| 参数 | 说明 | 默认 |
|------|------|------|
| `--no-images` | 跳过图片生成 | 开启 |
| `--no-subtitles` | 跳过字幕烧录 | 开启 |
| `--no-polish` | 跳过音频优化 | 开启 |
| `--motion` | 启用平移缩放动效 | 关闭 |

## 输出结构

```
output/{name}/
├── final/
│   ├── {name}.mp4           # 原速视频
│   ├── {name}_0_75x.mp4     # 慢放视频（如有）
│   └── {name}.srt           # 字幕文件
├── intermediate/
│   └── frames/              # 漫画图片
└── story.mp3                # TTS 音频
```

## 在 Claude Code 中使用

直接用自然语言描述需求：

```
把这段文字做成漫画视频：My friend Julia called me...
帮我用 story.txt 生成 ESL 学习视频，0.75 倍速
把这个音频转成漫画视频：~/Downloads/lesson.mp3
```

## 完整示例

```bash
# 生成完整 ESL 教学视频（0.75 倍速）
python ~/.claude/skills/esl-comic-video/scripts/make_video.py \
  --story ~/Documents/stories/coffee_morning.txt \
  --output ~/Videos/ESL \
  --name coffee_lesson \
  --speed 0.75

# 试运行（不执行，只显示命令）
python ~/.claude/skills/esl-comic-video/scripts/make_video.py \
  --story story.txt --dry-run
```

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| TTS 失败 | 检查网络连接；ElevenLabs 失败会自动回退到 Edge TTS |
| 图片生成失败 | 检查 OPENROUTER_API_KEY |
| ffmpeg 未找到 | `brew install ffmpeg` |
| 速度调整失败 | 确保 ffmpeg 版本 >= 4.0 |

## 相关文件

- 主脚本：`/Users/liuyishou/usr/projects/inbox/ESL-video/make_comic_video.py`
- 封装脚本：`~/.claude/skills/esl-comic-video/scripts/make_video.py`
- 环境配置：`/Users/liuyishou/usr/projects/inbox/ESL-video/.env`
