---
name: volcengine-tts
description: 使用火山引擎语音合成API将文字转换为语音,支持多种音色和语速调节。
allowed-tools: Bash(python:*), Read, Write
---

# 火山引擎 TTS 文字转语音

通过火山引擎语音合成 API 将文字转换为高质量语音音频。

## 快速开始

### 环境配置

设置火山引擎 AppId 和 Access Token：

```bash
export VOLC_TTS_APPID="your_app_id"
export VOLC_TTS_ACCESS_TOKEN="your_access_token"
```

或创建 `.env` 文件（放在 skill 根目录）：

```bash
VOLC_TTS_APPID=your_app_id
VOLC_TTS_ACCESS_TOKEN=your_access_token
```

### 获取凭证

1. 访问 https://console.volcengine.com/speech/app
2. 创建语音技术应用
3. 开通"语音合成"服务
4. 获取 AppId 和 Access Token

### 基础使用

```bash
cd .claude/skills/volcengine-tts
python scripts/tts.py "你好，欢迎使用火山引擎语音合成服务"
```

### 指定音色

```bash
# 使用通用女声（默认）
python scripts/tts.py "今天天气真好" --voice BV001_streaming

# 使用阳光男声
python scripts/tts.py "今天天气真好" --voice BV056_streaming

# 使用音色别名
python scripts/tts.py "今天天气真好" --voice yangguang
```

### 调整语速和音量

```bash
# 语速1.2倍，音量1.5倍
python scripts/tts.py "这是一段测试文字" --speed 1.2 --volume 1.5
```

## 工作流建议

当用户请求文字转语音时，遵循以下流程：

### Step 1: 理解需求

与用户确认：
- 要转换的文字内容
- 音色偏好（男声/女声/特定风格）
- 语速和音量要求
- 输出格式（mp3/wav/pcm）

### Step 2: 选择音色

根据用户需求选择合适的音色（通用版）：
- 通用女声：`BV001_streaming` 或 `--voice female`
- 通用男声：`BV002_streaming` 或 `--voice male`
- 阳光男声：`BV056_streaming` 或 `--voice yangguang`
- 温柔小哥：`BV033_streaming` 或 `--voice wenrou`
- 儒雅青年：`BV102_streaming` 或 `--voice ruya`

### Step 3: 调用脚本

```bash
cd .claude/skills/volcengine-tts
python scripts/tts.py "文字内容" --voice 音色ID --output output.mp3
```

### Step 4: 返回结果

脚本会生成音频文件并输出文件路径，将结果返回给用户。

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| text | 要转换的文字 | 必填 |
| --voice | 音色ID或别名 | BV001_streaming |
| --speed | 语速(0.5-2.0) | 1.0 |
| --volume | 音量(0.5-2.0) | 1.0 |
| --pitch | 音调(0.5-2.0) | 1.0 |
| --format | 输出格式: mp3/wav/pcm | mp3 |
| --output | 输出文件路径 | tts_[timestamp].mp3 |
| --encoding | 文本编码 | utf-8 |

## 常用音色列表

### 通用版音色（推荐）

| 音色ID | 别名 | 说明 |
|--------|------|------|
| `BV001_streaming` | female | 通用女声（默认） |
| `BV002_streaming` | male | 通用男声 |
| `BV056_streaming` | yangguang | 阳光男声 |
| `BV033_streaming` | wenrou | 温柔小哥 |
| `BV102_streaming` | ruya | 儒雅青年 |

## 依赖安装

```bash
cd .claude/skills/volcengine-tts
pip install -r scripts/requirements.txt
```

## 在 Claude Code 中使用

在 Claude Code 中直接说：

```
把这段文字转成语音：今天是个好日子
用男声朗读这段文字
帮我生成一段语音，内容是...
```

Claude 会自动调用该 skill 为你生成语音。

## 技术细节

- API文档: https://www.volcengine.com/docs/6561/79820
- API端点: `https://openspeech.bytedance.com/api/v1/tts`
- 协议: HTTP POST
- 采样率: 24000Hz
- 认证: Bearer Token (Bearer;{token})
- 返回格式: JSON (音频为 Base64 编码)

## 注意事项

1. 单次请求文本长度建议不超过500字
2. 长文本会自动分段处理
3. 生成的音频文件保存在指定目录
4. 请合理使用API调用次数

## 故障排查

如果遇到问题：
1. 确认 AppId 和 Access Token 已正确设置
2. 检查网络连接是否正常
3. 确认账号已开通语音合成服务
4. 查看错误信息中的详细提示
