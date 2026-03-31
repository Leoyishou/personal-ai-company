# 铅笔白板风 (Pencil Whiteboard)

手绘简笔画 + 铅笔音效擦除动画 + 配音解说的视频模板。

## 风格特点

- **视觉**：白板手绘简笔画风格（Nanobanana 生成）
- **动画**：Wipe 从左到右擦除显现（1.5秒）+ Ken Burns 微缩放
- **音效**：铅笔书写声配合擦除动画
- **配音**：擦除完成后开始，不与铅笔声重叠
- **转场**：淡入淡出（fade）

## 时间线结构

```
[铅笔音效 0-1.5s] → [配音 1.5s-结束]
     ↑                    ↑
   wipe动画           Ken Burns缩放
```

## 使用方式

### 1. 准备素材

**图片**（Nanobanana 生成）：
```bash
cd ~/.claude/skills/nanobanana-draw
python scripts/nanobanana_draw.py "Hand-drawn whiteboard sketch style, 9:16 vertical (1080x1920px), bold black marker with blue accents, pure white background. [场景描述]" --style "手绘白板" --subject "[主题]"
```

**配音**（volc-tts 生成）：
```bash
cd ~/.claude/skills/volc-tts
python scripts/tts.py --voice huopo -o output.mp3 "配音文案"
# 添加首尾静音
ffmpeg -y -i output.mp3 -af "adelay=800|800,apad=pad_dur=1" output_padded.mp3
```

**铅笔音效**：
- 位置：`~/.claude/agents/content-pr-department/assets/audio/sfx/pencil_writing.mp3`
- 来源：[Orange Free Sounds](https://orangefreesounds.com/pencil-writing-sound-effect/) (CC BY-NC 4.0)

### 2. 创建项目

```bash
cd /Users/liuyishou/usr/projects/inbox
cp -r ~/.claude/agents/content-pr-department/assets/templates/pencil-whiteboard/remotion-template [项目名]
cd [项目名]
npm install
```

### 3. 配置场景

编辑 `src/scenes.ts`：
```typescript
export const scenes = [
  { slide: "slides/01_hook.jpg", audio: "audio/hook.mp3", duration: 7.5 },
  { slide: "slides/02_xxx.png", audio: "audio/xxx.mp3", duration: 8 },
  // ...
];
```

**场景时长计算**：`绘制时间(1.5s) + 配音时长 + 缓冲(0.5s)`

### 4. 渲染导出

```bash
npx remotion render Main out/{YYYYMMDD}_铅笔白板_{主题}.mp4
```

## 文件命名规范

遵循 Nanobanana 命名格式：
```
{YYYYMMDD}_{风格}_{主题}_{序号}.{格式}
```

示例：
- `20260128_铅笔白板_保时捷5大车型.mp4`
- `20260128_铅笔白板_iPhone版本指南.mp4`

## 参数配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 绘制时长 | 1.5s | wipe 动画时长 |
| 铅笔音量 | 0.5 | 铅笔音效音量 |
| BGM 音量 | 0.08 | 背景音乐音量 |
| 转场时长 | 10帧 | 淡入淡出时长 |
| 分辨率 | 1080x1920 | 竖版视频 |
| 帧率 | 30fps | - |

## 适用场景

- 知识科普（产品对比、功能介绍）
- 列表盘点（Top 5、推荐清单）
- 流程说明（步骤教程）
- 概念解释（原理图解）

## 案例

- 保时捷5大经典车型
- iPhone 各版本对比指南
