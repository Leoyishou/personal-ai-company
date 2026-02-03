---
name: api-asr
description: "火山引擎语音识别 - 将音频/视频转文字，支持长音频分段识别。"
allowed-tools: Bash(python:*), Read
model: sonnet
tags: [asr, audio, volcengine, transcription]
---

# 火山引擎语音识别工具

通过火山引擎（豆包大模型）将音频/视频文件转换为文字，支持多种识别模式。

## 识别模式

| 模式 | 接口类型 | 最长时长 | 适用场景 |
|------|----------|----------|----------|
| streaming | WebSocket 实时流式 | ~2分钟 | 短音频、实时转录 |
| segment | 分段流式 | 无限制 | 长音频（推荐） |
| upload | HTTP 异步任务 | 4小时 | 需要音频 URL |
| auto | 自动选择 | - | 默认模式 |

**推荐**：对于长音频，使用 `segment` 模式，自动分割音频后逐段识别。

## 前置条件

### 流式模式（streaming）
1. 访问 [火山引擎语音控制台](https://console.volcengine.com/speech/app)
2. 创建应用，开通「语音识别大模型」服务
3. 获取 `APP ID` 和 `Access Token`

### 上传模式（upload）
1. 访问 [火山引擎语音控制台](https://console.volcengine.com/speech/app)
2. 开通「录音文件识别大模型」服务
3. 获取 `API Key`

## 快速开始

```bash
cd ~/.claude/skills/speech-recognition/scripts

# 自动选择模式（根据音频时长自动选择 streaming 或 segment）
python speech_recognition.py -i audio.mp3 -o result.txt

# 短音频：流式模式
python speech_recognition.py -i short.mp3 -m streaming -o result.txt

# 长音频：分段模式（推荐）
python speech_recognition.py -i long.mp4 -m segment -o result.srt -f srt

# 自定义分段时长（默认90秒）
python speech_recognition.py -i long.mp4 -m segment --segment-duration 60 -o result.json -f json

# 上传模式（需要音频公网 URL）
python speech_recognition.py -i audio.mp3 -m upload --audio-url "https://example.com/audio.mp3"
```

**注意**：使用时需要绕过代理：
```bash
ALL_PROXY="" HTTP_PROXY="" HTTPS_PROXY="" NO_PROXY="*" python speech_recognition.py ...
```

## 参数说明

| 参数 | 说明 | 默认值 |
|-----|------|-------|
| `--input`, `-i` | 输入音频/视频文件（必填） | - |
| `--output`, `-o` | 输出文件路径 | 标准输出 |
| `--format`, `-f` | 输出格式：txt/srt/vtt/json | txt |
| `--mode`, `-m` | 识别模式：auto/streaming/segment/upload | auto |
| `--segment-duration` | 分段模式下每段时长（秒） | 90 |
| `--language`, `-l` | 识别语言 | zh-CN |
| `--no-punc` | 不添加标点符号 | False |
| `--no-itn` | 不做数字规范化 | False |
| `--audio-url` | 音频的公网 URL（上传模式） | - |
| `--app-id` | APP ID（流式/分段模式） | 从环境变量读取 |
| `--token` | Access Token（流式/分段模式） | 从环境变量读取 |
| `--api-key` | API Key（上传模式） | 从环境变量读取 |
| `--hotword-id` | 热词表 ID | 从环境变量读取 |
| `--hotword-name` | 热词表名称 | 从环境变量读取 |

## 环境变量配置

在 `~/.claude/secrets.env` 中配置：

```bash
# 流式模式凭证
VOLC_ASR_APPID=your_app_id
VOLC_ASR_TOKEN=your_access_token

# 上传模式凭证
VOLC_ASR_API_KEY=your_api_key

# 热词管理 API 凭证（可选）
VOLC_ACCESS_KEY_ID=your_ak
VOLC_SECRET_ACCESS_KEY=your_sk

# 热词表（可选，在火山引擎控制台创建）
VOLC_ASR_HOTWORD_ID=your_hotword_table_id
VOLC_ASR_HOTWORD_NAME=your_hotword_table_name
```

## 热词功能

热词可提升特定词汇的识别准确率，特别适合专业术语、品牌名称等。

### 使用方式

**方式一：控制台创建**
1. 访问 [热词管理](https://console.volcengine.com/speech/hotword)
2. 上传热词文件，获取热词表 ID 或名称
3. 识别时使用 `--hotword-id` 或 `--hotword-name`

**方式二：API 创建（推荐）**
```bash
cd ~/.claude/skills/speech-recognition/scripts

# 1. 创建热词表（从预置 TXT 文件）
python hotword_manager.py create --app-id YOUR_APP_ID --name "AI术语" --file hotwords.txt

# 2. 或从 JSON 转换创建
python hotword_manager.py create --app-id YOUR_APP_ID --name "AI术语" --json hotwords.json

# 3. 列出已有热词表
python hotword_manager.py list --app-id YOUR_APP_ID

# 4. 删除热词表
python hotword_manager.py delete --app-id YOUR_APP_ID --table-id xxx
```

### 热词文件格式

**TXT 格式**（每行一个词，支持权重）：
```
Claude|10
GPT|10
大模型|9
思维链|8
```

- 格式：`热词|权重`（权重可选，1-10，默认 4）
- 每词 ≤ 10 字
- 每表最多 2000 词

### 预置热词

`scripts/hotwords.txt` 包含 80+ 个 AI 领域常见术语，可直接使用：
- 模型名：Claude, GPT, Gemini, DeepSeek, 豆包, Kimi 等
- 技术术语：LLM, RAG, Agent, Prompt, 思维链 等
- 工具名：Cursor, Copilot, LangChain, Vercel 等

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

## 注意事项

1. **自动模式**：默认根据音频时长自动选择模式（>2分钟使用 upload）
2. **上传模式需要公网 URL**：如果不提供 `--audio-url`，会自动上传到 transfer.sh 临时存储
3. **代理问题**：如使用 Surge 等代理，流式模式可能需要绕过代理
4. **支持格式**：MP3, WAV, M4A, MP4, MKV, MOV 等（自动用 ffmpeg 转换）

## 依赖安装

```bash
pip install websockets requests
brew install ffmpeg  # macOS
```
