# 手绘风格视频制作 SOP

## 一、内容准备
1. 确定核心信息点
2. 拆分为 5-7 个场景，每个场景一个核心观点
3. 撰写配音文案（每段 3-5 秒）

## 二、配音生成
```bash
# 使用 volc-tts skill 生成配音
# 音色推荐：huopo（活泼女声）、zhixing_emo（知性女声）
~/.claude/skills/volc-tts/tts.sh "文案内容" output.mp3 huopo

# 首尾加静音填充（开头 0.8s，结尾 1s）
ffmpeg -i input.mp3 -af "adelay=800|800,apad=pad_dur=1" output_padded.mp3
```

## 三、视觉素材生成
```bash
# 使用 Nanobanana (Gemini 3 Pro Image) 生成手绘风格图片
# Prompt 模板：
"白板手绘风格，黑色马克笔线条，简洁清晰，
竖版 1080x1920，内容：[场景描述]"
```

## 四、Remotion 项目搭建
```bash
npx create-video@latest project-name
cd project-name
```

**核心组件结构：**
```tsx
// SlideScene - 单个场景
const SlideScene = ({ src, audioSrc, audioDelay = 9 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Ken Burns 缩放效果
  const scale = interpolate(frame, [0, 5*fps], [1.05, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#fff" }}>
      <Sequence from={audioDelay}>
        <Audio src={staticFile(audioSrc)} />
      </Sequence>
      <Img
        src={staticFile(src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "contain",
          transform: `scale(${scale})`
        }}
      />
    </AbsoluteFill>
  );
};

// TransitionSeries 串联场景
<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={5.5*fps}>
    <SlideScene src="slide1.jpg" audioSrc="audio1.mp3" />
  </TransitionSeries.Sequence>
  <TransitionSeries.Transition
    presentation={fade()}
    timing={linearTiming({ durationInFrames: 15 })}
  />
  ...
</TransitionSeries>
```

## 五、音频配置
| 类型 | 音量 | 备注 |
|------|------|------|
| BGM | 10-15% | 循环播放，不抢配音 |
| TTS | 100% | 延迟 0.3s (9帧) 开始 |

## 六、渲染导出
```bash
npx remotion render CompositionId out/video.mp4
```

## 七、关键参数
- 分辨率：1080x1920（竖版）
- 帧率：30fps
- 场景时长：根据配音长度 + 0.5s 缓冲
- 转场时长：15帧（0.5秒）

## 八、素材位置
- BGM：`~/.claude/agents/content-pr-department/assets/audio/bgm/`
- 推荐口播 BGM：`calm/口播背景_轻柔.mp3`
