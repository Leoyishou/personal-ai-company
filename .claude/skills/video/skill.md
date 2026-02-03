---
name: video
description: "视频制作与处理 - 支持视频制作、极速发布、章节导航、封面生成等全流程"
---

# 视频制作与处理

综合视频处理工具，涵盖从制作到发布的全流程。

## 功能模块

| 模块 | 功能 | 触发场景 |
|------|------|----------|
| 极速发布 | 手机/电脑录制 → 自动转码、ASR、发布 | "快速录一个视频发布" |
| 视频制作 | 铅笔白板风等模板制作 | "做一个科普视频" |
| 章节导航 | 为视频添加章节进度条 | "给视频加章节" |
| 封面生成 | AI 封面 + 内嵌到视频 | 视频导出后自动执行 |

---

## 一、极速发布（Instant Publisher）

手机/电脑一键录制，自动转码、ASR 字幕、发布到 B 站/小红书。

### 启动服务

```bash
cd ~/.claude/skills/video/tools/instant-video-publisher
./start.sh
```

### 访问方式

| 设备 | 地址 |
|------|------|
| 电脑 | http://localhost:3456 |
| 手机 | http://<Mac-IP>:3456（可添加到桌面） |

### 工作流程

```
录制 → WebM转MP4 → ASR字幕 → 生成封面 → (可选)烧录字幕 → 发布
```

### 视频存储位置

```
~/Videos/instant-publish/
├── 2026-01-31T08-33-26_测试.webm    # 原始录制
├── 2026-01-31T08-33-26_测试.mp4     # 转码后
├── 2026-01-31T08-33-26_测试.srt     # ASR 字幕
├── 2026-01-31T08-33-26_测试_cover.jpg  # 封面
└── 2026-01-31T08-33-26_测试.json    # 任务元数据
```

---

## 二、视频制作

### 素材库位置

| 素材类型 | 路径 |
|----------|------|
| **Skill 模板** | `~/.claude/skills/video/templates/` |
| **内容公关部素材库** | `~/.claude/agents/content-pr-department/assets/` |
| **BGM** | `~/.claude/agents/content-pr-department/assets/audio/bgm/` |
| **音效** | `~/.claude/agents/content-pr-department/assets/audio/sfx/` |
| **铅笔音效** | `~/.claude/agents/content-pr-department/assets/audio/sfx/pencil_writing.mp3` |
| **口播 BGM** | `~/.claude/agents/content-pr-department/assets/audio/bgm/calm/口播背景_轻柔.mp3` |

### 项目输出位置

```
/Users/liuyishou/usr/projects/inbox/{项目名}/out/{YYYYMMDD}_{风格}_{主题}.mp4
```

### 支持的风格模板

| 风格ID | 名称 | 特点 | 适用场景 |
|--------|------|------|----------|
| `pencil-whiteboard` | 铅笔白板风 | 手绘简笔画 + 铅笔音效擦除 + 配音 | 知识科普、产品对比、列表盘点 |

### 视频制作工作流（必须遵循）

#### Step 1: 确认需求

收到视频制作请求后，确认：
- **风格**：用户指定的风格（如"铅笔白板风"）
- **主题**：视频主题（如"保时捷5大车型"）
- **场景列表**：每个场景的标题和配音文案

如果用户没有提供完整信息，使用 AskUserQuestion 询问。

#### Step 2: 创建项目

```bash
PROJECT_NAME="porsche-models"
PROJECT_DIR="/Users/liuyishou/usr/projects/inbox/$PROJECT_NAME"
SKILL_DIR="$HOME/.claude/skills/video"

# 复制模板
cp -r "$SKILL_DIR/templates/pencil-whiteboard" "$PROJECT_DIR"

# 复制音效（从内容公关部素材库）
ASSETS_DIR="$HOME/.claude/agents/content-pr-department/assets"
cp "$ASSETS_DIR/audio/sfx/pencil_writing.mp3" "$PROJECT_DIR/public/audio/pencil.mp3"
cp "$ASSETS_DIR/audio/bgm/calm/口播背景_轻柔.mp3" "$PROJECT_DIR/public/audio/bgm.mp3"

# 安装依赖
cd "$PROJECT_DIR"
npm install
```

#### Step 3: 生成配音

使用 volc-tts skill 为每个场景生成配音：

```bash
cd ~/.claude/skills/api-tts

# 为每个场景生成配音
python scripts/tts.py --voice huopo -o $PROJECT_DIR/public/audio/scene1_raw.mp3 "配音文案"

# 添加首尾静音（开头 0.8s，结尾 1s）
cd $PROJECT_DIR/public/audio
ffmpeg -y -i scene1_raw.mp3 -af "adelay=800|800,apad=pad_dur=1" scene1.mp3
rm scene1_raw.mp3
```

#### Step 4: 生成图片

使用 draw skill 生成手绘风格图片：

```bash
# 铅笔白板风 Prompt 模板：
# Hand-drawn whiteboard sketch style, 9:16 vertical (1080x1920px),
# bold black marker with blue accents, pure white background.
# [具体场景描述]

# 复制到项目
cp 生成的图片.png $PROJECT_DIR/public/slides/01_scene.png
```

#### Step 5: 配置场景

编辑 `$PROJECT_DIR/src/scenes.ts`：

```typescript
export const scenes: Scene[] = [
  { slide: "slides/01_hook.jpg", audio: "audio/hook.mp3", duration: 7.5 },
  { slide: "slides/02_scene1.png", audio: "audio/scene1.mp3", duration: 8 },
  // 场景时长 = 绘制时间(1.5s) + 配音时长 + 缓冲(0.5s)
];
```

**计算场景时长：**
```bash
# 获取音频时长
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $PROJECT_DIR/public/audio/scene1.mp3
# 场景时长 = 1.5 + 音频时长 + 0.5
```

#### Step 6: 渲染导出

```bash
cd $PROJECT_DIR

# 渲染视频
npx remotion render Main out/output.mp4

# 重命名（遵循命名规范）
DATE=$(date +%Y%m%d)
STYLE="铅笔白板"
SUBJECT="主题名"
mv out/output.mp4 "out/${DATE}_${STYLE}_${SUBJECT}.mp4"
```

#### Step 7: 生成封面并内嵌（必须）

视频导出后**必须**执行：

```bash
VIDEO_FILE="out/${DATE}_${STYLE}_${SUBJECT}.mp4"
COVER_FILE="out/${DATE}_${STYLE}_${SUBJECT}_cover.jpg"

# 方式1: 从视频截取封面（快速）
ffmpeg -y -ss 3 -i "$VIDEO_FILE" -frames:v 1 -q:v 2 "$COVER_FILE"

# 方式2: AI 生成封面（推荐，用 draw skill）

# 内嵌封面到视频
ffmpeg -y -i "$VIDEO_FILE" -i "$COVER_FILE" \
  -map 0:v -map 0:a -map 1 \
  -c:v copy -c:a copy -c:2 mjpeg \
  -disposition:2 attached_pic \
  "out/${DATE}_${STYLE}_${SUBJECT}_with_cover.mp4"

# 替换原文件
mv "$VIDEO_FILE" "out/${DATE}_${STYLE}_${SUBJECT}_no_cover.mp4"
mv "out/${DATE}_${STYLE}_${SUBJECT}_with_cover.mp4" "$VIDEO_FILE"
rm "out/${DATE}_${STYLE}_${SUBJECT}_no_cover.mp4"

# 验证（应该看到 3 个流：h264 + aac + mjpeg）
ffprobe -v quiet -show_streams "$VIDEO_FILE" | grep -E "codec_type|codec_name"
```

**封面尺寸参考：**

| 平台 | 尺寸 |
|------|------|
| B站 | 1280x720 (16:9) |
| 小红书 | 1080x1440 (3:4) |
| 抖音 | 1080x1920 (9:16) |

---

## 三、章节导航条

为视频添加章节导航条，显示当前章节进度和标题。

### 导航条样式

- 位置：视频底部（可配置）
- 高度：80px
- 背景：半透明黑色 (rgba(0,0,0,0.8))
- 进度条：蓝色 (#4A90E2)
- 文字：白色，24px

### 使用方法

#### 1. 准备章节配置

创建 `chapters.json`：
```json
{
  "chapters": [
    {"title": "开场介绍", "start": 0, "end": 10},
    {"title": "核心内容", "start": 10, "end": 30},
    {"title": "总结", "start": 30, "end": 40}
  ]
}
```

#### 2. 生成导航条

```bash
python ~/.claude/skills/video/scripts/add_chapter_nav.py \
  --input "输入视频.mp4" \
  --output "输出视频.mp4" \
  --chapters "chapters.json"
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--input` | 输入视频路径 |
| `--output` | 输出视频路径 |
| `--chapters` | 章节配置文件路径 |
| `--style` | 导航条样式 (default/minimal/full) |
| `--position` | 导航条位置 (top/bottom) |

---

## 四、参数配置

### 视频制作参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 绘制时长 | 1.5s | wipe 动画时长 |
| 铅笔音量 | 0.5 | 铅笔音效音量 |
| BGM 音量 | 0.08 | 背景音乐音量 |
| 转场时长 | 10帧 | 淡入淡出时长 |
| 分辨率 | 1080x1920 | 竖版视频 |
| 帧率 | 30fps | - |
| TTS 音色 | huopo | 活泼女声 |
| TTS 静音填充 | 开头 0.8s，结尾 1s | - |

### 章节导航条参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 高度 | 80px | 导航条高度 |
| 背景透明度 | 0.8 | 背景透明度 |
| 进度条颜色 | #4A90E2 | 进度条颜色 |
| 文字大小 | 24px | 章节标题字号 |
| 位置 | bottom | 导航条位置 |

---

## 五、文件命名规范

```
{YYYYMMDD}_{风格}_{主题}.mp4
{YYYYMMDD}_{风格}_{主题}_cover.jpg
```

示例：
- `20260128_铅笔白板_保时捷5大车型.mp4`
- `20260128_铅笔白板_保时捷5大车型_cover.jpg`

---

## 六、快速命令

```bash
# 创建视频项目
~/.claude/skills/video/scripts/create-project.sh <项目名> <风格>

# 添加章节导航
python ~/.claude/skills/video/scripts/add_chapter_nav.py \
  --input "原视频.mp4" \
  --output "带导航视频.mp4" \
  --chapters "chapters.json"
```

---

## 依赖

- Node.js + Remotion（视频制作）
- FFmpeg（视频处理）
- Python 3.8+（脚本工具）
- volc-tts skill（配音生成）
- draw skill（图片生成）
