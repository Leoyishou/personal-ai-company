---
name: supabase-upload
description: Supabase Storage 文件上传工具，支持本地文件和Base64上传，返回公开URL
allowed-tools: Bash(python:*), Read, Write
---

# Supabase Upload Skill

使用 Supabase Storage 上传文件，获取公开访问 URL。

## 快速开始

### 环境配置

在项目根目录 `.env` 文件中添加：

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-key
SUPABASE_BUCKET=uploads  # 可选，默认 uploads
```

### 上传文件

```bash
cd .claude/skills/supabase-upload
uv run python scripts/upload.py upload /path/to/image.png
```

只输出 URL：

```bash
uv run python scripts/upload.py upload /path/to/image.png --url-only
```

指定文件夹：

```bash
uv run python scripts/upload.py upload /path/to/image.png --folder images
```

### 列出文件

```bash
uv run python scripts/upload.py list --folder images
```

### 删除文件

```bash
uv run python scripts/upload.py delete images/filename.png
```

## 命令行参数

### upload

| 参数 | 说明 | 默认值 |
|------|------|--------|
| file | 本地文件路径 | 必填 |
| --folder, -f | 存储文件夹 | 根目录 |
| --name, -n | 自定义文件名 | 自动生成 UUID |
| --url-only | 只输出 URL | false |

### list

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --folder, -f | 文件夹路径 | 根目录 |

### delete

| 参数 | 说明 |
|------|------|
| path | 存储路径 |

## Python API

```python
from supabase_client import upload_file, upload_base64, delete_file, list_files

# 上传本地文件
url = upload_file("/path/to/image.png", folder="images")
print(f"Uploaded: {url}")

# 上传 Base64 数据
url = upload_base64(base64_data, content_type="image/png", folder="images")
print(f"Uploaded: {url}")

# 删除文件
delete_file("images/filename.png")

# 列出文件
files = list_files("images")
for f in files:
    print(f["name"])
```

## 与 digital-human 配合使用

上传图片和音频到 Supabase，获取 URL 后用于数字人视频生成：

```bash
# 上传图片
IMAGE_URL=$(uv run python .claude/skills/supabase-upload/scripts/upload.py upload avatar.png --url-only)

# 上传音频
AUDIO_URL=$(uv run python .claude/skills/supabase-upload/scripts/upload.py upload speech.mp3 --url-only)

# 生成数字人视频
uv run python .claude/skills/digital-human/scripts/digital_human.py \
  --image-url "$IMAGE_URL" \
  --audio-url "$AUDIO_URL"
```

## Supabase 配置说明

### 创建 Storage Bucket

1. 登录 Supabase Dashboard
2. 进入 Storage 页面
3. 创建新 Bucket（如 `uploads`）
4. 设置为 Public（公开访问）

### 获取 API Key

1. 进入 Project Settings > API
2. 复制 `anon` 或 `service_role` key
3. 复制 Project URL

## 错误处理

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| Missing SUPABASE_URL | 未设置环境变量 | 设置 SUPABASE_URL |
| Missing SUPABASE_KEY | 未设置访问密钥 | 设置 SUPABASE_KEY |
| File not found | 本地文件不存在 | 检查文件路径 |
| Upload failed | 上传失败 | 检查 Bucket 权限和网络 |
