# api-oss

阿里云 OSS 文件上传工具 - 将本地文件上传到 OSS 并返回公网 URL。

## 使用场景

- 上传音频文件供语音识别 API 使用（如火山引擎 ASR upload 模式）
- 上传图片获取公网链接
- 临时文件托管

## 核心功能

```bash
# 上传单个文件
python ~/.claude/skills/api-oss/scripts/upload.py /path/to/file.mp3

# 输出示例
https://imagehosting4picgo.oss-cn-beijing.aliyuncs.com/tmp/file_a1b2c3.mp3
```

## 环境变量

从 `~/.claude/secrets.env` 读取：

- `ALIYUN_OSS_ACCESS_KEY_ID`
- `ALIYUN_OSS_ACCESS_KEY_SECRET`
- `ALIYUN_OSS_BUCKET` (default: imagehosting4picgo)
- `ALIYUN_OSS_REGION` (default: oss-cn-beijing)

## 依赖

```bash
pip install oss2
```

## 上传路径规则

文件上传到 `tmp/` 目录下，文件名格式：`{原文件名}_{8位随机字符}.{扩展名}`

例如：`audio.mp3` → `tmp/audio_a1b2c3d4.mp3`
