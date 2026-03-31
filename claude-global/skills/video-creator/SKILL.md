---
name: video-creator
description: 创作完整的数字人解说视频。支持剧本生成、IP形象生成、TTS语音、背景音乐、数字人视频、Remotion合成。
allowed-tools: Bash(*), Bash(playwright-cli:*), Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, AskUserQuestion, Task(nanobanana-draw), Task(volcengine-tts), Task(supabase-upload), Task(digital-human), Task(bgm-search)
---

# 数字人解说视频创作工具

创作完整的数字人解说视频，从剧本到最终成片的全流程自动化。

## 重要原则

1. **实时数据优先**：涉及股价、新闻、时事等内容，**必须用 `playwright-cli` 获取实时数据**，不依赖 WebSearch 缓存
2. **剧本必须用户确认**：生成剧本后必须展示给用户确认（含数据来源+获取时间），用户同意后才能继续下一步
3. **数据真实性**：不可编造数据，必须标注数据来源和时间
4. **字幕与音频同步**：必须使用Whisper语音识别获取精确时间戳，不可手动估算
5. **绿幕背景**：IP形象必须使用绿幕背景，便于后期抠图合成
6. **背景音乐音量**：BGM音量控制在解说音量的15-20%，不能盖过解说声音

---

## 视频风格规范

### 画面布局（竖屏 9:16，1080×1920）

```
┌────────────────────────────────────────┐
│                                        │
│        【内容插图区域】                  │
│         (占画面 50%)                    │
│         宽度与视频一致                   │
│         完整显示不裁剪                   │
│                                        │
├────────────────────────────────────────┤
│                                        │
│        【数字人形象区域】                │
│         (占画面 50%)                    │
│         透明背景叠加在深蓝科技背景上      │
│         带网格线装饰                     │
│                                        │
│    ┌──────────────────────────────┐    │
│    │      字幕文字（白色居中）      │    │ ← 底部字幕
│    └──────────────────────────────┘    │
└────────────────────────────────────────┘
```

### 分辨率与编码

| 参数 | 规格 |
|------|------|
| 分辨率 | **1080×1920** (竖屏 9:16) |
| 帧率 | 30fps |
| 编码 | H.264 |
| 音频 | AAC, 44100Hz |

### 字幕样式

- **位置**: 视频底部（bottom: 60px）
- **对齐**: 居中
- **字体**: 白色，36-38px，PingFang SC / Microsoft YaHei
- **阴影**: 黑色阴影增强可读性
- **同步**: 必须与音频精确同步

---

## 完整工作流程

### Step 1: 了解需求

与用户确认以下信息：
- **主题方向**: 科技解说/产品介绍/知识分享/新闻解读/财经分析
- **视频时长**: 30秒/60秒/90秒（建议不超过90秒）
- **语言风格**: 专业严谨/轻松幽默/通俗易懂

### Step 2: 获取实时数据（关键步骤）

**⚠️ 重要**：如果主题涉及股价、新闻、财经、时事等内容，**必须使用 `playwright-cli` 获取实时数据**，不要依赖 WebSearch 的缓存结果！

#### 使用 playwright-cli 获取实时数据

**股票/财经数据：**
```bash
# 打开股票页面获取实时股价
playwright-cli open "https://finance.yahoo.com/quote/HOOD"
playwright-cli snapshot
# 截图保存（可选）
playwright-cli screenshot --filename=stock_data.png
```

**新闻热点：**
```bash
playwright-cli open "https://news.google.com/search?q=关键词"
playwright-cli snapshot
```

**科技资讯：**
```bash
playwright-cli open "https://www.theverge.com"
playwright-cli snapshot
```

**通用搜索：**
```bash
playwright-cli open "https://www.google.com"
playwright-cli snapshot
playwright-cli fill e1 "搜索关键词"
playwright-cli press Enter
playwright-cli snapshot
```

#### 数据提取要点

1. 从 snapshot 中提取关键数据（价格、日期、百分比等）
2. **记录数据获取时间**（精确到分钟）
3. **记录数据来源URL**
4. 将提取的数据整理成结构化信息，供 Step 3 使用

#### 补充搜索（可选）

如需更多背景信息，可补充使用 WebSearch：
```
WebSearch: "小米股票 2026年 分析师评级 目标价"
```

### Step 3: 生成解说剧本（需用户确认）

**基于 Step 2 获取的实时数据**生成剧本：

```json
{
  "title": "视频标题",
  "duration_seconds": 60,
  "data_source": {
    "url": "https://finance.yahoo.com/quote/HOOD",
    "fetch_time": "2026-02-05 21:30",
    "key_data": {
      "current_price": "$76.25",
      "day_change": "-3.2%"
    }
  },
  "segments": [
    {
      "id": 1,
      "text": "这段解说词内容...",
      "illustration_prompt": "对应的插图描述"
    }
  ],
  "full_script": "完整的解说词文本..."
}
```

**剧本要求**：
- 开头3秒抓住注意力（提问/悬念/痛点）
- 中间内容逻辑清晰，信息密度适中
- 结尾有总结或行动号召
- 数据必须真实准确

⚠️ **必须展示剧本给用户确认，包含以下信息：**

```
剧本已生成，请确认以下内容：

**视频标题**: xxx

**实时数据**（通过 playwright-cli 获取）:
- 数据来源: https://finance.yahoo.com/quote/HOOD
- 获取时间: 2026-02-05 21:30
- 当前股价: $76.25
- 今日涨跌: -3.2%

**完整剧本**:
1. xxx
2. xxx
...

⚠️ 股价等实时数据可能已发生变化，请确认是否需要更新。

确认后将开始生成IP形象、语音、插图等素材。
```

**只有用户确认后，才能继续执行后续步骤！**

### Step 4: 确认/生成IP数字人形象

IP形象有三种获取方式：

#### 方式一：用户直接提供

用户可以直接提供现成的IP形象图片，要求：
- 绿幕背景（标准绿色 #00B140）
- 3D卡通风格
- 正面或3/4侧面
- 嘴巴微张便于口型同步

#### 方式二：照片 + 文字描述生成

```bash
cd .claude/skills/nanobanana-draw
uv run python scripts/nanobanana_draw.py \
  "将这张照片中的人物转换成3D皮克斯风格的卡通形象，保持人物五官特征，穿着米白色连帽卫衣，嘴巴微张便于口型同步，背景使用纯绿色(#00B140)绿幕" \
  --image user_photo.jpg \
  --save-dir output/video-creator/<project-name>
```

#### 方式三：照片 + 参考图 + 描述生成

```bash
cd .claude/skills/nanobanana-draw
uv run python scripts/nanobanana_draw.py \
  "将第一张图片中的人物转换成第二张图片的3D卡通风格，保持人物五官特征和性别，服装参考第二张图片的风格，嘴巴微张便于口型同步，背景使用纯绿色(#00B140)绿幕" \
  --image user_photo.jpg \
  --style-image style_reference.png \
  --save-dir output/video-creator/<project-name>
```

**IP形象关键要求**：
- ✅ 背景必须是纯绿色幕布（#00B140）
- ✅ 嘴巴微张（便于口型同步）
- ✅ 保持用户五官特征
- ✅ 分辨率至少 512x512

### Step 5: 选择音色并生成TTS语音

先询问用户偏好的音色：

**可用音色列表**：

| 音色代号 | Voice ID | 描述 |
|---------|----------|------|
| female | BV001_streaming | 通用女声（成熟稳重）|
| male | BV002_streaming | 通用男声（成熟稳重）|
| yangguang | BV056_streaming | 阳光男声（年轻活力）|
| wenrou | BV033_streaming | 温柔小哥（温和亲切）|
| ruya | BV102_streaming | 儒雅青年（知性儒雅）|

```bash
cd .claude/skills/volcengine-tts
uv run python scripts/tts.py "${full_script}" \
  --voice yangguang \
  --speed 1.1 \
  --output output/video-creator/<project-name>/audio/narration.mp3
```

### Step 6: 搜索并下载背景音乐

使用 bgm-search skill 搜索适合视频氛围的背景音乐：

**根据视频主题选择关键词**：

| 视频类型 | 推荐搜索词 |
|---------|-----------|
| 财经分析 | technology corporate, business ambient |
| 科技解说 | electronic futuristic, digital ambient |
| 知识分享 | inspiring uplifting, gentle background |
| 新闻解读 | news documentary, cinematic ambient |
| 产品介绍 | modern corporate, upbeat technology |

```bash
cd .claude/skills/bgm-search

# 搜索并下载背景音乐（时长匹配视频长度）
uv run python scripts/search.py "technology corporate ambient" \
  --tag music \
  --duration 60-180 \
  --limit 3 \
  --download \
  --output ../../output/video-creator/<project-name>/bgm/
```

**背景音乐选择原则**：
- ✅ 时长应≥视频时长（Remotion会自动循环或截断）
- ✅ 选择无歌词的纯音乐，避免干扰解说
- ✅ 节奏平稳，不要过于激烈或突变
- ✅ 注意许可证（CC0 或 CC BY 可商用）

### Step 7: 上传素材到Supabase

```bash
cd .claude/skills/supabase-upload

# 上传IP形象
IMAGE_URL=$(uv run python scripts/upload.py upload ip_avatar.png --folder video-creator --url-only)

# 上传音频
AUDIO_URL=$(uv run python scripts/upload.py upload narration.mp3 --folder video-creator --url-only)
```

### Step 8: 生成数字人视频

调用火山引擎 OmniHuman1.5 生成数字人说话视频：

```bash
cd .claude/skills/digital-human
uv run python scripts/digital_human.py \
  --image-url "$IMAGE_URL" \
  --audio-url "$AUDIO_URL" \
  --vertical \
  --output output/video-creator/<project-name>/digital_human/avatar.mp4 \
  --max-polls 40
```

**关键参数说明**：
- `--vertical` - 生成 9:16 竖屏视频 (1080x1920)，避免人物被裁剪
- 也可用 `--width 1080 --height 1920` 自定义尺寸

**注意**：
- 生成时间较长，需要耐心等待
- 如果超时，使用任务ID继续查询直到完成
- **使用 `--vertical` 可确保人物完整显示，不会被裁剪**

### Step 9: 绿幕抠图（关键步骤）

将绿幕视频替换为深蓝色背景的WebM格式（与Remotion背景色一致）：

#### 9.1 检测实际绿幕颜色

**重要**：火山引擎生成的绿幕颜色可能不是标准的 #00B140，需要先检测：

```bash
# 提取第一帧
ffmpeg -i avatar.mp4 -vf "select=eq(n\,0)" -vframes 1 -update 1 frame_sample.png -y

# 采样绿幕区域颜色（左上角）
ffmpeg -i frame_sample.png -vf "crop=1:1:20:20,format=rgb24" -f rawvideo -pix_fmt rgb24 - 2>/dev/null | xxd -p
# 输出示例：0a903e 表示颜色为 #0a903e
```

#### 9.2 绿幕替换为深蓝色背景

```bash
# 获取视频尺寸和时长
VIDEO_SIZE=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 avatar.mp4)
# 示例输出：1664,1248
DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 avatar.mp4)

ffmpeg -i avatar.mp4 \
  -filter_complex "[0:v]chromakey=0x0a8f3f:0.08:0.05,despill=type=green:mix=0.5[fg];color=c=0x0a1628:s=${VIDEO_SIZE}:d=${DURATION}[bg];[bg][fg]overlay=0:0:shortest=1" \
  -c:v libvpx-vp9 \
  -b:v 2M \
  avatar_transparent.webm -y
```

**关键参数说明**：
- `chromakey=0x0a8f3f:0.08:0.05` - 抠除绿色背景
  - `0x0a8f3f` - 实际检测到的绿幕颜色（火山引擎常用此色）
  - `0.08` - 相似度（**越小越精确，减少衣服/肤色污染**）
  - `0.05` - 混合度（边缘柔和度）
- `despill=type=green:mix=0.5` - **必须添加**，去除绿色溢出，防止肤色/衣服变色
- `color=c=0x0a1628` - 创建深蓝色背景（与Remotion背景色一致）
- `overlay=0:0:shortest=1` - 将抠图后的人物叠加到深蓝色背景上

**常见绿幕颜色参考**：
| 来源 | 颜色值 | 推荐参数 |
|------|--------|----------|
| 火山引擎OmniHuman | `0x0a8f3f` | `chromakey=0x0a8f3f:0.08:0.05,despill=type=green:mix=0.5` |
| 标准绿幕 | `0x00B140` | `chromakey=0x00B140:0.15:0.05,despill=type=green:mix=0.5` |
| 纯绿色 | `0x00FF00` | `chromakey=green:0.2:0.08,despill=type=green:mix=0.5` |

⚠️ **注意**：
- 不要尝试输出透明WebM（yuva420p），Windows上的VP9编码器不支持alpha通道！
- 如果衣服/肤色仍有污染，可进一步降低相似度参数（如0.06），但可能在边缘留绿边

### Step 10: 生成内容插图

使用手绘图表风格生成插图：

**推荐提示词模板**：

```
Hand-drawn infographic, sketchnote style, doodle art, whiteboard style.
White background, black ink outlines, loose strokes, minimalist coloring with pastel blue and soft red accents.
Content: [具体内容描述]
Visual metaphors, arrows and diagrams, cute stick figures.
Clean composition, high resolution.
All text must be in Simplified Chinese.
```

**示例**：

```bash
cd .claude/skills/nanobanana-draw

# 场景1：股价下跌
uv run python scripts/nanobanana_draw.py \
  "Hand-drawn infographic, sketchnote style, doodle art. White background, black ink outlines, loose strokes, pastel blue and soft red accents. Content: A stock chart showing dramatic decline with red downward arrow, sad stick figure investor. Chinese text labels. Clean composition. All text in Simplified Chinese." \
  --save-dir output/video-creator/<project-name>/illustrations
```

### Step 11: 使用Whisper获取精确字幕时间戳

**必须使用语音识别获取时间戳，不可手动估算**：

```python
import whisper
import json

model = whisper.load_model('base')
result = model.transcribe('narration.mp3', language='zh', word_timestamps=True)

segments = []
for seg in result['segments']:
    segments.append({
        'startMs': round(seg['start'] * 1000),
        'endMs': round(seg['end'] * 1000),
        'text': seg['text'].strip()
    })

print(json.dumps(segments, ensure_ascii=False, indent=2))
```

根据识别结果更新Remotion组件中的字幕时间轴。

### Step 12: Remotion合成最终视频

#### 12.1 准备素材到public目录

```bash
mkdir -p public/<project-name>
cp avatar_transparent.webm public/<project-name>/
cp narration.mp3 public/<project-name>/
cp illustrations/scene_*.jpg public/<project-name>/
cp bgm/*.mp3 public/<project-name>/bgm.mp3  # 背景音乐
```

#### 12.2 创建/更新Remotion组件

组件布局要点：
- 上方50%：插图区域，`width: 100%`, `objectFit: contain`
- 下方50%：数字人区域，深蓝科技背景+网格线
- 底部：字幕居中，白色带阴影
- 字幕时间轴使用Whisper识别结果
- **音频**：解说音频 + 背景音乐（需控制音量比例）

```tsx
// 关键样式
// 插图区域
<div style={{ height: "50%", backgroundColor: "#0d1a2d" }}>
  <Img style={{ width: "100%", maxHeight: "100%", objectFit: "contain" }} />
</div>

// 数字人区域
<div style={{
  height: "50%",
  background: "linear-gradient(180deg, #1a2a4a 0%, #0a1628 100%)"
}}>
  <Video src={staticFile("avatar_transparent.webm")} />
</div>

// 字幕
<p style={{
  color: "#ffffff",
  textAlign: "center",
  textShadow: "0 2px 8px rgba(0,0,0,0.8)"
}}>
  {currentSubtitle.text}
</p>

// 音频 - 解说语音（主音量）
<Audio src={staticFile("<project-name>/narration.mp3")} volume={1} />

// 音频 - 背景音乐（15-20%音量，不要盖过解说）
<Audio src={staticFile("<project-name>/bgm.mp3")} volume={0.15} loop />
```

**背景音乐音量控制说明**：

| 场景 | 推荐音量 | 说明 |
|-----|---------|-----|
| 解说为主 | 0.10 - 0.15 | 背景音乐只做氛围，不干扰解说 |
| 情感渲染 | 0.20 - 0.25 | 需要音乐增强情感时适当提高 |
| 片头片尾 | 0.30 - 0.50 | 无解说时可提高音乐音量 |

**动态音量控制**（可选）：

```tsx
import { interpolate, useCurrentFrame } from "remotion";

// 片头3秒背景音乐渐入
const bgmVolume = interpolate(
  frame,
  [0, 90],  // 0-3秒
  [0, 0.15],
  { extrapolateRight: "clamp" }
);

<Audio src={staticFile("bgm.mp3")} volume={bgmVolume} loop />
```

#### 12.3 渲染视频

```bash
cd project-root
npx remotion render CompositionName output/video-creator/<project-name>/final_video.mp4 --codec=h264
```

---

## 输出目录结构

```
output/video-creator/<project-name>/
├── script.json                    # 剧本文件
├── ip_avatar.png                  # IP数字人形象（绿幕）
├── audio/
│   └── narration.mp3              # TTS解说音频
├── bgm/
│   └── background.mp3             # 背景音乐
├── illustrations/
│   ├── scene_01.jpg               # 场景插图
│   ├── scene_02.jpg
│   └── ...
├── digital_human/
│   └── avatar.mp4                 # 数字人原始视频（绿幕）
├── public/                        # Remotion素材目录
│   ├── avatar_transparent.webm    # 抠图后的透明视频
│   ├── narration.mp3
│   ├── bgm.mp3                    # 背景音乐
│   └── scene_*.jpg
└── final_video.mp4                # 最终输出视频
```

---

## 常见问题处理

### 1. 数字人肤色发绿

**原因**：绿幕抠图时没有添加despill处理

**解决**：确保ffmpeg命令包含 `despill=green` 滤镜

```bash
ffmpeg -i input.mp4 -vf "chromakey=0x00B140:0.25:0.05,despill=green" ...
```

### 2. 字幕与音频不同步

**原因**：手动估算字幕时间

**解决**：必须使用Whisper语音识别获取精确时间戳

### 3. 插图被裁剪

**原因**：使用了 `objectFit: cover`

**解决**：改用 `objectFit: contain`，配合 `width: 100%`

### 4. 数字人生成超时

**原因**：API处理时间较长

**解决**：记录task_id，使用单独脚本继续查询直到完成

---

## 依赖技能

- `playwright-cli` - 浏览器自动化（获取实时数据）
- `nanobanana-draw` - AI绘图（支持图片参考和风格迁移）
- `volcengine-tts` - 语音合成
- `bgm-search` - 背景音乐搜索（基于 Freesound API）
- `supabase-upload` - 文件上传
- `digital-human` - 数字人视频生成
- Remotion - 视频合成框架
- Whisper - 语音识别（用于字幕同步）
