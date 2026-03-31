---
name: stickman-video
description: 生成火柴人风格短视频。自动生成解说词、TTS语音、背景音乐、火柴人插图，使用Remotion合成视频。
allowed-tools: Bash(python:*), Bash(npm:*), Bash(npx:*), Bash(ffmpeg:*), Bash(playwright-cli:*), Read, Write, Edit
---

# 火柴人短视频生成器 (Stickman Video Generator)

自动生成火柴人风格的短视频，整合实时数据获取、解说词生成、TTS语音、背景音乐搜索、AI绘图和Remotion视频合成。

## 视频规格（必须严格遵守）

### 技术参数
| 参数 | 规格 |
|------|------|
| 分辨率 | **960×720** (横屏 4:3) |
| 编码 | H.264/AVC（兼容性好，所有播放器都能播放） |
| 帧率 | 30fps |
| 音频 | AAC, 44100Hz, 单声道 |

### 画面布局
```
┌────────────────────────────────────────────────┐
│ 内容总结(黑色)              个人观点，无不良引导(红色) │ ← 顶部栏 36px 浅灰背景
├────────────────────────────────────────────────┤
│                                                │
│                                                │
│              【火柴人插图区域】                   │ ← 中间区域 白色/浅灰背景
│                 居中显示                        │
│                                                │
│                                                │
├────────────────────────────────────────────────┤
│           字幕文字（黑色大号）                    │ ← 底部渐变背景(透明→浅灰)
└────────────────────────────────────────────────┘
```

### 顶部栏说明
- **左上角**: 内容总结/金句，如"这就是散户"、"这就是所谓的实在人"（不是视频标题！）
- **右上角**: 固定文字"个人观点，无不良引导"（红色）

### 字幕样式（重要）
- **背景**: 渐变，从透明渐变到浅灰 `linear-gradient(to bottom, rgba(200,200,200,0) 0%, rgba(200,200,200,0.8) 30%, rgba(180,180,180,0.95) 100%)`
- **字体颜色**: 黑色 `#222`（不是白色！）
- **字体大小**: 36px
- **高度**: 约 100px

### 字幕拆分规则（重要！）
- **短句原则**: 每条字幕不超过15个字，长句必须拆分成多条短字幕
- **同图多字幕**: 同一张图片可以对应多条短字幕，字幕切换时图片保持不动
- **时间分配**: 每个segment的音频时长按比例分配给多条短字幕
- **示例**:
  - ❌ 错误: "Robinhood，一只曾经翻了五倍的妖股，从去年的30美元，一路飙升到154美元"
  - ✅ 正确: 拆分为4条短字幕
    - "Robinhood" (15%)
    - "一只曾经翻了五倍的妖股" (35%)
    - "从去年的30美元" (25%)
    - "一路飙升到154美元" (25%)

### 图片切换效果（重要！）
- **过渡动画**: 新场景切入时使用 0.3秒淡入 + 轻微缩放(1.05→1.0)
- **同场景内**: 字幕切换时图片保持静止，无任何动画
- **避免闪烁**: 只有 scene_id 变化时才触发图片动画

### 火柴人插图风格
- **线条**: 黑白铅笔素描风格，手绘感
- **背景**: 纯白或浅灰
- **特征**: 可加天使光环、披风、思维气泡等创意元素
- **标注**: 可用简单英文标注 (如 "LOW PAY", "HIGH PAY")
- **表情**: 简单但传神（开心、难过、困惑等）

### 音频要求（重要）
- **TTS语音**: 先生成所有分段音频，然后用 ffmpeg **合并成一个连贯的音频文件**
- **背景音乐**: 音量控制在语音的 15-20%
- **字幕同步**: 字幕必须与语音时间轴精确对应

## 工作流程

### Step 0: 获取实时数据（如需要）

**如果视频主题涉及实时信息（股价、新闻、体育、热点等），使用 WebSearch 获取最新数据。**

#### 搜索方式

**推荐使用 WebSearch（更准确）：**
```
# 股票数据
WebSearch: "HOOD stock price today"
WebSearch: "Robinhood HOOD 股票 最新消息 2026"

# 新闻热点
WebSearch: "今日热点新闻"

# 体育赛事
WebSearch: "NBA 今日比赛结果"
```

**备选使用 playwright-cli（需要截图或复杂交互时）：**
```bash
playwright-cli open "https://finance.yahoo.com/quote/HOOD"
playwright-cli snapshot
playwright-cli screenshot --filename=stock_data.png
```

#### 数据提取要点
1. 从搜索结果中提取关键数据（价格、日期、百分比等）
2. **记录数据获取时间**，用于后续用户确认
3. 将提取的数据整理成结构化信息，供 Step 1 使用
4. **注意**：WebSearch 结果通常更准确、更及时

### Step 1: 生成解说词脚本

**基于 Step 0 获取的实时数据**，生成分段解说词。**按语义分组，不是每句一张图**。

**⚠️ 视觉节奏要求 (Visual Pacing):**

1.  **合理数量**: 图片数量要与视频时长匹配，**每张图展示 5-8 秒**为宜
    - 30秒视频 → 4-6 张图
    - 60秒视频 → 8-10 张图
    - 90秒视频 → 12-15 张图
2.  **避免过多**: 不要为每句话配一张图，图片过多会导致画面跳跃、观感混乱
3.  **避免过少**: 一张图不应超过 15 秒，否则画面单调乏味
4.  **语义分组**: 按内容主题分组配图，相关的几句话共用一张图

```json
{
  "meta": {
    "title": "这就是所谓的实在人",
    "bgm_mood": "sad",  // 可选: happy, sad, tense, relaxing, upbeat
    "bgm_tag": "piano", // 搜索关键词
    "character_anchor": "simple stick figure with a red tie" // 角色一致性特征
  },
  "scenes": [
    {
      "id": 1,
      "description": "引入-工作态度",
      "image_prompt": "火柴人坐在办公桌前埋头工作，桌上左边一小叠钱标注LOW PAY...",
      "image_file": "scene_01.png"
    }
  ],
  "segments": [
    {
      "id": 1,
      "scene_id": 1,
      "subtitles": [
        { "text": "有一种员工", "ratio": 0.4 },
        { "text": "叫做职场实在人", "ratio": 0.6 }
      ]
    },
    {
      "id": 2,
      "scene_id": 1,
      "subtitles": [
        { "text": "不管你开多少工资", "ratio": 1.0 }
      ]
    }
  ]
}
```

**字幕数据结构说明**:
- `subtitles`: 每个segment可包含多条短字幕
- `text`: 字幕文字（不超过15字）
- `ratio`: 该字幕在segment音频时长中的占比（所有ratio之和应为1.0）

### Step 1.5: 用户确认脚本（必须！）

**⚠️ 重要：生成脚本后必须暂停，让用户确认后再继续！**

使用 AskUserQuestion 工具询问用户：
1. 展示完整的解说词脚本内容
2. **明确标注数据来源和获取时间**（来自 Step 0）
3. 让用户确认内容的**真实性**和**时效性**
4. 用户可以选择：确认继续、修改内容、或取消

示例提问：
```
脚本已生成，请确认以下内容：

**标题**: xxx

**实时数据**（通过 playwright-cli 获取）:
- 数据来源: https://finance.yahoo.com/quote/HOOD
- 获取时间: 2026-02-05 21:30
- 当前股价: $76.25
- 今日涨跌: -3.2%

**解说词**:
1. xxx
2. xxx
...

⚠️ 股价等实时数据可能已发生变化，请确认是否需要更新。

请确认脚本内容是否准确，确认后将开始生成语音和图片。
```

**只有用户确认后，才能继续执行后续步骤！**

### Step 2: TTS 语音合成

**关键：生成连贯音频而非分段播放**

```bash
# 1. 生成各段音频
for i in {1..N}; do
  uv run python .claude/skills/volcengine-tts/scripts/tts.py "第i段文字" \
    --voice BV002_streaming --output audio/segment_0${i}.mp3
done

# 2. 合并成一个连贯音频（重要！）
ffmpeg -i "concat:segment_01.mp3|segment_02.mp3|..." -acodec copy audio/full_audio.mp3

# 或使用文件列表方式合并
echo "file 'segment_01.mp3'" > list.txt
echo "file 'segment_02.mp3'" >> list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy audio/full_audio.mp3
```

### Step 3: 搜索背景音乐

**根据 Step 1 脚本中的 mood 和 tag 搜索** (不要硬编码 "relaxing")。

```
# 示例：使用脚本中的变量
uv run python .claude/skills/bgm-search/scripts/search.py \
  --mood "{script.meta.bgm_mood}" \
  --tag "{script.meta.bgm_tag}" \
  --duration "30-180" --limit 1 --download --output bgm/
```

### Step 4: 生成火柴人插图

使用 nanobanana-draw skill。

**Prompt 构造规则**:

1. **通用风格**: `Hand-drawn infographic illustration, sketchnote doodle style, black ink marker outlines...`
2. **角色锚点**: 必须包含 Step 1 定义的 `character_anchor` (例如 `simple stick figure with a red tie`)，确保主角形象统一。
3. **场景描述**: 具体的动作和隐喻。

**Prompt 构造模板**: 将以下模板中的变量替换为 Step 1 脚本中的具体内容：

```
Hand-drawn infographic illustration, sketchnote doodle style, black ink marker outlines with spot pastel color highlights, white background, 

featuring {script.meta.character_anchor}, {scene.description}, 

loose hand-drawn look, minimalist line art texture, expressive cute cartoon style, visual metaphors, [optional: with thought bubble containing simple icon related to the topic], [optional: with hand-written text label related to the topic connected by an arrow]
```

### Step 5: 视频合成

使用项目根目录的 Remotion 配置。

```
cd /项目根目录
npx remotion render StickmanXXX output/video.mp4 --codec=h264
```

**Remotion 防闪烁规范 (参考 `remotion-best-practices`):**

- **图片**: 仅在 `scene_id` 变化时才应用淡入动画 (`<SceneImage>`)，同场景内使用静态组件 (`<StaticImage>`)。
- **字幕**: **禁止** 任何淡入淡出动画，必须硬切显示，确保流畅阅读。
- **布局**: 顶部栏和底部栏必须始终覆盖在图片层之上。

## Remotion 组件要点

```tsx
// 分辨率必须是 960x720
<Composition
  id="StickmanVideo"
  width={960}
  height={720}
  fps={30}
  ...
/>

// 布局结构
<AbsoluteFill style={{ backgroundColor: '#f5f5f5' }}>
  {/* 顶部标题栏 - 36px 高 */}
  <div style={{ height: 36, backgroundColor: 'rgba(200,200,200,0.9)' }}>
    <span style={{ color: '#333' }}>{title}</span>
    <span style={{ color: '#d64541' }}>个人观点，无不良引导</span>
  </div>

  {/* 中间图片区域 */}
  <div style={{ top: 36, bottom: 80 }}>
    <Img src={currentImage} />
  </div>

  {/* 底部字幕条 - 80px 高 */}
  <div style={{ height: 80, backgroundColor: 'rgba(50,50,50,0.95)' }}>
    <span style={{ color: '#fff', fontSize: 32 }}>{subtitle}</span>
  </div>

  {/* 一个连贯的音频文件 */}
  <Audio src={staticFile('audio/full_audio.mp3')} volume={1} />
  <Audio src={staticFile('bgm/background.mp3')} volume={0.15} />
</AbsoluteFill>
```

## 输出文件结构

```
output/stickman-video/<topic>/
├── script.json              # 解说词脚本
├── audio/
│   ├── segment_01.mp3       # 分段语音
│   ├── segment_02.mp3
│   ├── ...
│   └── full_audio.mp3       # 合并后的完整语音（关键！）
├── bgm/
│   └── background.mp3       # 背景音乐
├── images/
│   ├── scene_01.png         # 场景图片
│   ├── scene_02.png
│   └── ...
└── 最终视频.mp4              # 960x720 H.264 编码
```

## 常见问题

### 音频不连贯
- 原因：分段播放 TTS 音频
- 解决：用 ffmpeg 合并所有音频为一个文件，Remotion 只播放这一个文件

### 分辨率错误
- 必须是 960x720 横屏
- 不要用 1080x1920 竖屏

### 字幕不同步
- 需要记录每段音频的实际时长
- 用 ffprobe 获取：`ffprobe -show_entries format=duration audio.mp3`
- 根据时长计算每段字幕的起止帧

### 画面闪烁（重要！）
- **问题**: 每句字幕切换时画面都闪一下
- **原因**: 每个 Sequence 的图片和字幕都有独立的淡入动画，frame 从 0 开始导致重新淡入
- **解决**:
  1. **图片**: 只在场景切换时使用带淡入动画的组件，同场景内保持静止
  2. **字幕**: 完全去掉淡入动画，直接显示

```tsx
// 场景图片组件 - 带平滑过渡动画
const SceneImage: React.FC<{ imagePath: string; isNewScene: boolean }> = ({ imagePath, isNewScene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 只有新场景才有动画
  const opacity = isNewScene
    ? interpolate(frame, [0, fps * 0.3], [0, 1], { extrapolateRight: 'clamp' })
    : 1;

  // 轻微的缩放动画，让过渡更自然
  const scale = isNewScene
    ? interpolate(frame, [0, fps * 0.4], [1.05, 1], { extrapolateRight: 'clamp' })
    : 1;

  return (
    <div style={{ opacity, transform: `scale(${scale})` }}>
      <Img src={staticFile(imagePath)} />
    </div>
  );
};

// 字幕：不要任何动画，直接显示
const Subtitle = ({ text }) => (
  <div style={{ /* 样式 */ }}>
    <span>{text}</span>  {/* 无 opacity 动画 */}
  </div>
);

// 使用时判断是否是新场景
const isNewScene = segment.scene_id !== prevSegment?.scene_id;
<SceneImage imagePath={imagePath} isNewScene={isNewScene} />
```

## 注意事项

1. **⚠️ 实时数据**: 涉及股价、新闻、体育等实时信息时，**优先使用 WebSearch 获取最新数据**（更准确），playwright-cli 仅在需要截图或复杂交互时使用
2. **⚠️ 脚本确认**: 生成脚本后**必须让用户确认**再继续，明确展示数据来源和获取时间，让用户验证真实性和时效性
3. **分辨率**: 必须是 960×720，不是竖屏
4. **音频**: 必须合并成一个文件，不能分段播放
5. **编码**: 使用 H.264/AVC，加参数 `--codec=h264`（兼容性好，所有播放器都能直接播放）
6. **字幕**: 与语音时间轴精确同步
7. **图片数量**: 由语义决定，不硬性限制
8. **画面过渡**: 图片只在场景切换时淡入，同场景内字幕切换不能闪烁
