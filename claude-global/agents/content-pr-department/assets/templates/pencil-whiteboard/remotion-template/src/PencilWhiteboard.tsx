import {
  AbsoluteFill,
  Img,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  Sequence,
  staticFile,
  Easing,
} from "remotion";
import { Audio } from "@remotion/media";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { scenes } from "./scenes";

// 绘制效果场景组件
interface DrawSceneProps {
  src: string;
  audioSrc?: string;
}

const DrawScene = ({ src, audioSrc }: DrawSceneProps) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 绘制时长（帧数）- 1.5秒
  const drawDuration = Math.round(1.5 * fps);

  // 配音在绘制完成后开始（不重叠）
  const voiceStart = drawDuration;

  // Wipe 擦除效果：从左到右逐渐显现
  const drawProgress = interpolate(
    frame,
    [0, drawDuration],
    [0, 100],
    {
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    }
  );

  // Ken Burns 缩放（绘制完成后开始）
  const scale = interpolate(
    frame,
    [drawDuration, 5 * fps],
    [1.02, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "#fff" }}>
      {/* 铅笔音效 - 只在绘制期间播放 */}
      <Sequence durationInFrames={drawDuration}>
        <Audio src={staticFile("audio/pencil.mp3")} volume={0.5} />
      </Sequence>

      {/* 配音 - 绘制完成后开始 */}
      {audioSrc && (
        <Sequence from={voiceStart}>
          <Audio src={staticFile(audioSrc)} />
        </Sequence>
      )}

      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <div
          style={{
            width: "100%",
            height: "100%",
            overflow: "hidden",
          }}
        >
          <Img
            src={staticFile(src)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
              transform: `scale(${scale})`,
              clipPath: `inset(0 ${100 - drawProgress}% 0 0)`,
            }}
          />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// 主组合
export const PencilWhiteboardComposition = () => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill>
      {/* 背景音乐 */}
      <Audio src={staticFile("audio/bgm.mp3")} volume={0.08} loop />

      <TransitionSeries>
        {scenes.map((scene, index) => (
          <>
            {index > 0 && (
              <TransitionSeries.Transition
                key={`transition-${index}`}
                presentation={fade()}
                timing={linearTiming({ durationInFrames: 10 })}
              />
            )}
            <TransitionSeries.Sequence
              key={`scene-${index}`}
              durationInFrames={Math.round(scene.duration * fps)}
            >
              <DrawScene src={scene.slide} audioSrc={scene.audio} />
            </TransitionSeries.Sequence>
          </>
        ))}
      </TransitionSeries>
    </AbsoluteFill>
  );
};
