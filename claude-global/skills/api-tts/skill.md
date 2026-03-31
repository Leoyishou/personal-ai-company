---
name: api-tts
description: "火山引擎（豆包）语音合成 TTS，支持多种音色、语速调节、多种音频格式。"
allowed-tools: Bash(python:*), Read
model: sonnet
tags: [tts, audio, volcengine]
---

# 火山引擎（豆包）语音合成 TTS

通过火山引擎 TTS API 将文本转换为语音。支持多种音色、语速调节、多种音频格式。

## 环境配置

在 `~/.claude/secrets.env` 中配置：

```bash
VOLC_TTS_APPID=你的appid
VOLC_TTS_TOKEN=你的access_token
```

获取方式：https://console.volcengine.com/speech/service/8

## 基础使用

```bash
cd ~/.claude/skills/api-tts
python scripts/tts.py "你好，这是一段测试语音"
```

### 指定音色

```bash
python scripts/tts.py --voice cancan "你好世界"
python scripts/tts.py --voice yangguang "大家好"
```

### 调整语速

```bash
python scripts/tts.py --speed 1.2 "这段话会快一点"
python scripts/tts.py --speed 0.8 "这段话会慢一点"
```

### 指定输出格式和路径

```bash
python scripts/tts.py --encoding wav --output /tmp/hello.wav "你好"
python scripts/tts.py -e mp3 -o ~/Desktop/speech.mp3 "测试"
```

### 列出可用音色

```bash
python scripts/tts.py --list-voices
```

### 从标准输入读取

```bash
echo "这是一段测试" | python scripts/tts.py
```

## 工作流（必须遵循）

收到用户的语音合成请求后：

### Step 1: 确认合成内容
- 文本内容（最大约300字符）
- 音色偏好（默认：cancan 灿灿女声）
- 语速要求（默认：1.0）

### Step 2: 调用脚本

```bash
cd ~/.claude/skills/api-tts
python scripts/tts.py --voice <音色> --speed <语速> "文本内容"
```

### Step 3: 返回结果
- 告知用户生成的音频文件路径
- 用 `open` 命令播放（macOS）

## 常用音色

| 别名 | 描述 | voice_type | 状态 |
|------|------|------------|------|
| yangyang | 炀炀 | BV705_streaming | ★ 已购买（2027-01到期） |
| mengwa | 奶气萌娃 | BV051_streaming | ★ 已购买（2027-01到期） |
| huopo | 活泼女声（视频配音） | BV005_streaming | ★ 已购买（2027-01到期） |
| female | 通用女声（默认） | BV001_streaming | 免费 |
| male | 通用男声 | BV002_streaming | 免费 |

更多音色：https://www.volcengine.com/docs/6561/1257544

## 参数说明

| 参数 | 说明 | 范围 |
|------|------|------|
| --voice, -v | 音色ID或别名 | 见音色列表 |
| --speed, -s | 语速 | 0.1 ~ 2.0 |
| --encoding, -e | 音频格式 | mp3/wav/pcm/ogg_opus |
| --rate, -r | 采样率 | 8000/16000/24000 |
| --output, -o | 输出路径 | 任意路径 |

## 长文本处理

单次合成限制约300字符。超长文本需分段合成：

```python
# 脚本会自动检查长度并提示
# 建议按句号/段落分割后逐段合成
```

## 故障排查

1. "authenticate request" 错误 → 检查 appid 和 token
2. "quota exceeded" → 试用额度用完，需开通正式版
3. "Fail to feed text" → 检查 voice_type 是否正确
4. 文本超长 → 分段合成，每段 < 300字符
