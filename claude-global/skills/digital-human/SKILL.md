---
name: digital-human
description: 使用火山引擎OmniHuman1.5生成数字人视频,输入IP形象图片+音频,输出数字人说话视频。
allowed-tools: Bash(python:*), Read, Write
---

# 数字人视频生成工具 (OmniHuman1.5)

通过火山引擎 OmniHuman1.5 API 生成数字人说话视频。输入一张IP形象图片和一段音频,输出数字人口型同步的说话视频。

## ⚠️ 重要说明

**API 要求使用 URL 参数**：图片和音频必须是公开可访问的 URL。本地文件需要先上传到 Supabase Storage。

## 快速开始

### 环境配置

1. 设置火山引擎 AK/SK：

```bash
export VOLC_ACCESSKEY="your_access_key"
export VOLC_SECRETKEY="your_secret_key"
```

2. 配置 Supabase（用于上传本地文件）：

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-service-role-key"
export SUPABASE_BUCKET="video-magic"
```

### 使用 URL（推荐）

```bash
cd .claude/skills/digital-human
uv run python scripts/digital_human.py \
  --image-url "https://your-storage.com/avatar.png" \
  --audio-url "https://your-storage.com/speech.mp3"
```

### 使用本地文件（自动上传到 Supabase）

```bash
uv run python scripts/digital_human.py \
  --image "path/to/avatar.png" \
  --audio "path/to/speech.mp3"
```

### 添加提示词控制动作

```bash
uv run python scripts/digital_human.py \
  --image-url "https://..." \
  --audio-url "https://..." \
  --prompt "人物微笑,轻微点头"
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --image | 本地图片路径（自动上传） | - |
| --image-url | 图片URL（推荐） | - |
| --audio | 本地音频路径（自动上传） | - |
| --audio-url | 音频URL（推荐） | - |
| --prompt | 提示词(控制动作、表情) | 无 |
| --output | 输出视频路径 | output/digital_human_[timestamp].mp4 |
| **--width** | **输出视频宽度** | 自动（根据输入图片） |
| **--height** | **输出视频高度** | 自动（根据输入图片） |
| **--vertical** | **竖屏快捷方式 (1080x1920)** | false |
| --callback-url | 回调URL | 无 |
| --no-download | 不下载视频,只输出URL | false |
| --no-query | 不查询状态,仅提交任务 | false |
| --poll-interval | 轮询间隔秒数 | 30 |
| --max-polls | 最大轮询次数 | 20 |
| --debug | 保存调试信息 | false |

### 输出尺寸控制

默认情况下，输出视频尺寸根据输入图片自动计算，可能导致人物被裁剪。

**推荐：使用 `--vertical` 生成竖屏视频**

```bash
# 生成 9:16 竖屏视频 (1080x1920)
uv run python scripts/digital_human.py \
  --image-url "https://..." \
  --audio-url "https://..." \
  --vertical

# 自定义尺寸
uv run python scripts/digital_human.py \
  --image-url "https://..." \
  --audio-url "https://..." \
  --width 1280 --height 1920
```

**常用尺寸预设**：

| 用途 | 宽度 | 高度 | 比例 |
|-----|------|------|------|
| 抖音/TikTok | 1080 | 1920 | 9:16 |
| 视频号 | 1080 | 1920 | 9:16 |
| B站横屏 | 1920 | 1080 | 16:9 |
| 正方形 | 1080 | 1080 | 1:1 |

## 工作流程

1. **上传文件**（如使用本地文件）
   - 自动调用 supabase-upload skill 上传到 Supabase Storage
   - 获取公开访问 URL

2. **提交任务**
   - 使用 `image_url` 和 `audio_url` 参数调用 CVSubmitTask
   - 返回 task_id

3. **轮询结果**
   - 每 30 秒调用 CVGetResult 查询状态
   - 状态为 `done` 时获取 video_url

4. **下载视频**
   - 自动下载到 output 目录

## 支持的输入格式

### 图片
- 格式: PNG, JPG, JPEG
- 建议: 正面照,面部清晰
- 支持: 真人、动漫、宠物等

### 音频
- 格式: MP3, WAV, M4A
- 建议: 清晰的人声,时长 5-60 秒

## 技术细节

- API端点: `https://visual.volcengineapi.com`
- Action: `CVSubmitTask` / `CVGetResult`
- Version: `2022-08-31`
- req_key: `jimeng_realman_avatar_picture_omni_v15`
- 认证: 火山引擎 HMAC-SHA256 签名
- **参数格式**: `image_url` + `audio_url`（不是 base64）

## 故障排查

### 错误 50215 "Input invalid for this service"
- **原因**: 使用了 base64 参数而不是 URL 参数
- **解决**: 确保使用 `image_url` 和 `audio_url`

### 图片/音频 URL 无法访问
- **原因**: Supabase bucket 未设为 public
- **解决**: 在 Supabase Dashboard 设置 bucket 为 Public

### 其他问题
1. 确认 AK/SK 已正确设置
2. 确认 Supabase 配置正确
3. 检查图片是否为清晰的正面照
4. 检查音频是否为清晰的人声
