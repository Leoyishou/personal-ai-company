---
name: volcengine-asr
description: 火山引擎（豆包）语音识别服务。支持音频/视频文件转文字，输出带时间戳的字幕格式（SRT/VTT/TXT）。中文识别效果优秀，支持标点和数字规范化。
allowed-tools: Bash(python:*), Bash(ffmpeg*), Read, Write, Glob
model: sonnet
---

# 火山引擎 ASR 语音识别工具

通过火山引擎（豆包大模型）将音频/视频文件转换为文字，支持输出 SRT/VTT 字幕或纯文本。

## 前置条件

需要在火山引擎控制台创建应用并获取凭证：

1. 访问 [火山引擎语音控制台](https://console.volcengine.com/speech/app)
2. 创建应用，开通「语音识别大模型」服务
3. 获取 `APP ID` 和 `Access Token`
4. Resource ID 使用：`volc.bigasr.sauc.duration`

## 快速开始

### 基础用法

```bash
cd /Users/liuyishou/.claude/skills/volcengine-asr/scripts

# 转录音频文件
python volcengine_asr.py --input audio.mp3 --output result.txt

# 输出 SRT 字幕
python volcengine_asr.py --input video.mp4 --output subtitles.srt --format srt

# 输出 VTT 字幕
python volcengine_asr.py --input audio.wav --output subtitles.vtt --format vtt
```

### 视频转录

```bash
# 自动提取音频并转录
python volcengine_asr.py --input video.mp4 --output transcript.txt

# 生成字幕文件
python volcengine_asr.py --input video.mp4 --output video.srt --format srt
```

## 参数说明

| 参数 | 说明 | 默认值 |
|-----|------|-------|
| `--input`, `-i` | 输入音频/视频文件（必填） | - |
| `--output`, `-o` | 输出文件路径 | 自动生成 |
| `--format`, `-f` | 输出格式：txt/srt/vtt/json | txt |
| `--language`, `-l` | 识别语言 | zh-CN |
| `--no-punc` | 不添加标点符号 | False |
| `--no-itn` | 不做数字规范化 | False |

## 支持的音频格式

- **直接支持**: WAV, PCM (16kHz, 16bit, mono)
- **自动转换**: MP3, M4A, AAC, FLAC, OGG, MP4, MKV, MOV 等

视频文件会自动提取音频轨道进行转录。

## 输出格式示例

### TXT（纯文本）
```
大家好，欢迎来到今天的分享。
我们今天要讨论的主题是人工智能。
```

### SRT（字幕）
```
1
00:00:00,000 --> 00:00:02,500
大家好，欢迎来到今天的分享。

2
00:00:02,500 --> 00:00:05,000
我们今天要讨论的主题是人工智能。
```

### VTT（WebVTT 字幕）
```
WEBVTT

00:00:00.000 --> 00:00:02.500
大家好，欢迎来到今天的分享。

00:00:02.500 --> 00:00:05.000
我们今天要讨论的主题是人工智能。
```

## 工作流建议

### Step 1: 检查输入文件
确认音频/视频文件存在且格式正确。

### Step 2: 选择输出格式
- 纯文字稿：`--format txt`
- 视频字幕：`--format srt` 或 `--format vtt`
- 后续处理：`--format json`

### Step 3: 执行转录
```bash
cd /Users/liuyishou/.claude/skills/volcengine-asr/scripts
python volcengine_asr.py --input /path/to/file --output /path/to/output --format srt
```

## 配合其他 Skill 使用

### 配合 video-chapter-nav
```bash
# 先转录生成字幕
python volcengine_asr.py --input video.mp4 --output video.srt --format srt

# 再生成章节导航（使用 video-chapter-nav skill）
```

### 配合 esl-comic-video
```bash
# 先转录音频获取文本
python volcengine_asr.py --input narration.mp3 --output script.txt

# 再用文本生成漫画视频
```

## 环境配置

在 `.env` 文件中配置凭证：

```bash
VOLC_ASR_APPID=your_app_id
VOLC_ASR_TOKEN=your_access_token
VOLC_ASR_RESOURCE_ID=volc.bigasr.sauc.duration
```

或者使用命令行参数：
```bash
python volcengine_asr.py --input audio.mp3 --app-id xxx --token xxx
```

## 依赖安装

```bash
pip install websockets aiofiles
```

还需要 ffmpeg 用于音频格式转换：
```bash
brew install ffmpeg  # macOS
```

## 注意事项

1. **音频格式**：非 PCM 格式会自动用 ffmpeg 转换
2. **文件大小**：大文件会分片处理，无时长限制
3. **网络要求**：需要能访问 `openspeech.bytedance.com`
4. **计费**：按音频时长计费，详见火山引擎定价
5. **代理问题**：如果使用 Surge 等代理，需要绕过：
   ```bash
   ALL_PROXY="" HTTP_PROXY="" HTTPS_PROXY="" NO_PROXY="*" python volcengine_asr.py ...
   ```

## 错误处理

| 错误 | 原因 | 解决方案 |
|-----|------|---------|
| Missing credentials | 未配置凭证 | 检查 .env 或命令行参数 |
| Connection failed | 网络问题 | 检查网络连接 |
| Invalid audio format | 音频格式不支持 | 确保安装了 ffmpeg |
