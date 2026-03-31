# Volcengine TTS - 火山引擎文字转语音

基于火山引擎语音合成API的文字转语音工具，支持多种中英文音色。

## 功能特点

- 支持中英文文字转语音
- 多种音色可选（男声/女声）
- 可调节语速、音量、音调
- 支持 MP3/WAV/PCM 输出格式
- 流式输出支持

## 快速开始

### 1. 安装依赖

```bash
cd .claude/skills/volcengine-tts
pip install -r scripts/requirements.txt
```

### 2. 配置凭证

从[火山引擎语音技术控制台](https://console.volcengine.com/speech/app)获取 AppId 和 Access Token。

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的凭证
```

或设置环境变量：

```bash
export VOLC_TTS_APPID="your_app_id"
export VOLC_TTS_ACCESS_TOKEN="your_access_token"
```

### 3. 使用

```bash
# 基本使用
python scripts/tts.py "你好，世界"

# 指定音色
python scripts/tts.py "Hello" --voice amanda

# 调整语速
python scripts/tts.py "这是快速播放" --speed 1.5

# 指定输出文件
python scripts/tts.py "保存为指定文件" --output my_audio.mp3

# 查看所有音色
python scripts/tts.py --list-voices
```

## 音色列表

### 中文女声
| 预设名 | 音色ID | 特点 |
|--------|--------|------|
| tianmei | zh_female_tianmeixiaoyuan_moon_bigtts | 甜美小媛 |
| shuangkuai | zh_female_shuangkuaisisi_moon_bigtts | 爽快思思 |
| wanwan | zh_female_wanwanxiaohe_moon_bigtts | 湾湾小何 |
| qingche | zh_female_qingche_moon_bigtts | 清澈女声 |
| shaonv | zh_female_shaonvxiaoxin_moon_bigtts | 少女小新 |

### 中文男声
| 预设名 | 音色ID | 特点 |
|--------|--------|------|
| chunhou | zh_male_chunhou_emo_moon_bigtts | 醇厚男声 |
| yangguang | zh_male_yangguangqingsong_moon_bigtts | 阳光青松 |
| yuanqing | zh_male_yuanqingjieceng_moon_bigtts | 远庆街层 |
| shaonian | zh_male_shaonianshuifen_moon_bigtts | 少年水分 |

### 英文音色
| 预设名 | 音色ID | 特点 |
|--------|--------|------|
| amanda | en_female_amanda_moon_bigtts | 女声Amanda |
| ryan | en_male_ryan_moon_bigtts | 男声Ryan |
| emily | en_female_emily_moon_bigtts | 女声Emily |
| john | en_male_john_moon_bigtts | 男声John |

## API 使用

```python
from scripts.tts_client import synthesize, synthesize_stream

# 一次性合成
audio_data = synthesize(
    text="你好，世界",
    voice="zh_female_tianmeixiaoyuan_moon_bigtts",
    speed=1.0,
    volume=1.0,
)

# 保存文件
with open("output.mp3", "wb") as f:
    f.write(audio_data)

# 流式合成
for chunk in synthesize_stream("长文本..."):
    # 处理音频块
    pass
```

## 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| text | - | 要转换的文字 | 必填 |
| --voice | -v | 音色ID或预设名 | tianmei |
| --speed | -s | 语速(0.5-2.0) | 1.0 |
| --volume | - | 音量(0.5-2.0) | 1.0 |
| --pitch | - | 音调(0.5-2.0) | 1.0 |
| --format | -f | 输出格式 | mp3 |
| --output | -o | 输出文件路径 | 自动生成 |
| --list-voices | - | 列出所有音色 | - |

## 注意事项

1. 单次请求文本长度建议不超过500字
2. 需要开通火山引擎语音合成服务
3. 注意API调用配额限制

## License

MIT
