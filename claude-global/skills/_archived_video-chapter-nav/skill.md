---
name: video-chapter-nav
description: "视频章节导航条 - 为视频顶部添加章节导航，实时显示当前播放位置。"
---

# 视频章节导航条工具

为视频顶部添加章节导航条，实时显示当前播放位置，当前章节高亮显示。

## 效果示例

```
┌─────────────────────────────────────────────────────────┐
│ 1.引言 │ [2.正文]  │ 3.总结 │  ← 导航条（蓝色=当前章节）
├─────────────────────────────────────────────────────────┤
│                                                         │
│                    视频内容区域                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 快速开始

```bash
cd ~/.claude/skills/video-chapter-nav/scripts

# 方式一：使用章节配置文件
python add_chapter_nav.py -i video.mp4 -o output.mp4 -c chapters.json

# 方式二：直接指定章节
python add_chapter_nav.py -i video.mp4 -o output.mp4 \
  --chapters "0:00 引言,1:30 正文,5:00 总结"
```

## 章节配置格式

### JSON 文件格式

```json
[
  {"index": 1, "start": "0:00", "title": "引入与痛点"},
  {"index": 2, "start": "1:00", "title": "产品介绍"},
  {"index": 3, "start": "2:30", "title": "核心特性"},
  {"index": 4, "start": "4:30", "title": "安全机制"},
  {"index": 5, "start": "5:30", "title": "总结展望"}
]
```

支持的时间格式：
- `M:SS` - 分:秒（如 `1:30`）
- `H:MM:SS` - 时:分:秒（如 `1:05:30`）
- `start_ms` - 毫秒（如 `90000`）
- `start_sec` - 秒（如 `90`）

### 命令行字符串格式

```
"时间 标题,时间 标题,..."
```

示例：`"0:00 引言,1:30 正文,5:00 总结"`

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-i`, `--input` | 输入视频文件（必填） | - |
| `-o`, `--output` | 输出视频文件（必填） | - |
| `-c`, `--config` | 章节配置 JSON 文件 | - |
| `--chapters` | 章节字符串 | - |
| `--nav-height` | 导航条高度（像素） | 50 |
| `--crf` | 视频质量（0-51，越小越高） | 23 |
| `--preset` | 编码速度 | fast |
| `--keep-images` | 保留生成的导航条图片 | False |
| `--image-dir` | 指定图片保存目录 | 临时目录 |

## 工作原理

1. **分析视频** - 获取分辨率和时长
2. **生成导航条图片** - 为每个章节生成一张 PNG（当前章节蓝色高亮）
3. **FFmpeg 叠加** - 使用 overlay 滤镜 + enable 条件按时间切换图片

### 核心 FFmpeg 命令

```bash
ffmpeg -y -i input.mp4 \
  -i nav_chapter_1.png -i nav_chapter_2.png -i nav_chapter_3.png \
  -filter_complex "
    [0:v][1:v]overlay=0:0:enable='between(t,0,60)'[v1];
    [v1][2:v]overlay=0:0:enable='between(t,60,150)'[v2];
    [v2][3:v]overlay=0:0:enable='gte(t,150)'[v3]
  " \
  -map "[v3]" -map "0:a" -c:a copy -c:v libx264 -preset fast -crf 23 \
  output.mp4
```

## 配合其他 Skill 使用

### 配合 ASR 自动生成章节

```bash
# 1. 先用语音识别获取文本
cd ~/.claude/skills/speech-recognition/scripts
python speech_recognition.py -i video.mp4 -o transcript.txt -f txt

# 2. 根据内容手动或用 AI 划分章节，生成 chapters.json

# 3. 添加导航条
cd ~/.claude/skills/video-chapter-nav/scripts
python add_chapter_nav.py -i video.mp4 -o output.mp4 -c chapters.json
```

### 配合 B站上传

```bash
# 1. 添加章节导航
python add_chapter_nav.py -i video.mp4 -o video_with_nav.mp4 -c chapters.json

# 2. 上传到 B站
cd ~/.claude/skills/biliup-publish
biliup upload video_with_nav.mp4 --title "视频标题" --tid 231
```

## 自定义样式

### 修改高亮颜色

编辑脚本中的颜色值：

```python
# 当前章节背景色（RGBA）
fill=(59, 130, 246, 255)  # Tailwind blue-500

# 其他章节文字色
fill=(180, 180, 180, 255)  # 灰色
```

### 修改导航条背景

```python
# 半透明黑色背景
img = Image.new('RGBA', (width, height), (0, 0, 0, 180))
```

### 修改字体大小

```python
font = ImageFont.truetype(font_path, 20)  # 修改 20 为其他值
```

## 依赖

- Python 3.7+
- Pillow（PIL）
- FFmpeg

```bash
pip install Pillow
brew install ffmpeg  # macOS
```

## 中文字体支持

脚本自动查找系统中文字体，支持：

| 系统 | 字体 |
|------|------|
| macOS | Hiragino Sans GB, PingFang |
| Linux | Noto Sans CJK, Droid Sans |
| Windows | 微软雅黑, 黑体 |

## 注意事项

1. **章节数量**：建议 3-7 个，过多会导致文字过小
2. **标题长度**：每个标题建议 2-6 个字，过长会被截断
3. **视频时长**：脚本自动获取，最后一个章节延伸到视频结尾
4. **编码时间**：取决于视频长度和 preset 设置

## 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 中文显示方块 | 字体不支持中文 | 检查字体路径是否正确 |
| 导航条位置错误 | 视频分辨率获取失败 | 确保 ffprobe 可用 |
| 编码失败 | FFmpeg 版本过低 | 升级 FFmpeg |
| 章节时间错误 | 时间格式不对 | 使用 M:SS 或 H:MM:SS 格式 |
