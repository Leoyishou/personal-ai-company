# Video Creator 视频创作工具

将绿幕解说视频自动转换为带技术图和字幕的完整竖屏视频。

## 功能

- **绿幕抠图**: FFmpeg chromakey 滤镜，MP4 → 透明 WebM
- **语音转录**: Whisper 自动生成 SRT 字幕
- **AI 生图**: Nanobanana 根据内容生成技术插图
- **视频合成**: Remotion 合成最终视频

## 依赖

- FFmpeg (带 libvpx-vp9 和 libopus)
- Node.js 18+
- uv (Python 包管理器)
- Whisper (通过 uv 安装)

## 快速开始

### 方式一：使用一键脚本

```bash
bash .claude/skills/video-creator/scripts/create_video.sh input.mp4 ./my-project
```

### 方式二：分步执行

#### 1. 绿幕抠图

```bash
ffmpeg -i input.mp4 \
    -vf "chromakey=0x00FF00:0.3:0.1" \
    -c:v libvpx-vp9 \
    -pix_fmt yuva420p \
    -c:a libopus \
    public/character.webm
```

#### 2. 音频转录

```bash
ffmpeg -i public/character.webm -vn -acodec pcm_s16le -ar 16000 -ac 1 temp.wav -y
uv run whisper temp.wav --language Chinese --model base --output_format srt --output_dir public
mv public/temp.srt public/subtitles.srt
```

#### 3. 生成技术图

使用 Claude 调用 nanobanana-draw 技能，根据字幕内容生成技术插图。

#### 4. 渲染视频

```bash
npm install
npm run build
```

## 项目结构

```
.claude/skills/video-creator/
├── SKILL.md              # 技能定义
├── README.md             # 说明文档
├── scripts/
│   ├── create_video.sh   # 一键创建脚本
│   ├── green_screen_to_webm.sh  # 绿幕抠图
│   └── transcribe.sh     # 音频转录
└── templates/
    ├── package.json      # Remotion 项目配置
    ├── index.ts          # 入口文件
    ├── Root.tsx          # 组合定义
    └── VideoComposition.tsx  # 视频组件
```

## FFmpeg 绿幕参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| color | 绿幕颜色 | 0x00FF00 |
| similarity | 相似度 (0-1) | 0.3 |
| blend | 边缘混合 (0-1) | 0.1 |

常见绿幕颜色:
- 纯绿: `0x00FF00`
- 深绿: `0x008000`
- 草绿: `0x7CFC00`

## 输出格式

- 分辨率: 720x1280 (9:16 竖屏)
- 帧率: 30fps
- 视频编码: H.264
- 音频编码: AAC
