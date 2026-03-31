import { useState, useEffect, useCallback } from "react";
import {
  AbsoluteFill,
  Img,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Sequence,
  delayRender,
  continueRender,
  spring,
} from "remotion";
import { Video } from "@remotion/media";
import { parseSrt } from "@remotion/captions";
import type { Caption } from "@remotion/captions";

// 图片段落配置类型
type ImageSegment = {
  id: number;
  startMs: number;
  endMs: number;
  topic: string;
  content: string;
  imageFile: string;
};

type SegmentsConfig = {
  segments: ImageSegment[];
};

type VideoCompositionProps = {
  characterVideo?: string;
  subtitlesFile?: string;
  segmentsFile?: string;
  backgroundColor?: string;
  accentColor?: string;
};

export const VideoComposition: React.FC<VideoCompositionProps> = ({
  characterVideo = "character.webm",
  subtitlesFile = "subtitles.srt",
  segmentsFile = "segments.json",
  backgroundColor = "#1a1a2e",
  accentColor = "#00d4ff",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const [captions, setCaptions] = useState<Caption[]>([]);
  const [segments, setSegments] = useState<ImageSegment[]>([]);
  const [handle] = useState(() => delayRender());

  // 加载字幕
  const fetchCaptions = useCallback(async () => {
    try {
      const response = await fetch(staticFile(subtitlesFile));
      const text = await response.text();
      const { captions: parsed } = parseSrt({ input: text });
      setCaptions(parsed);
    } catch (e) {
      console.error("Failed to load captions:", e);
      setCaptions([]);
    }
  }, [subtitlesFile]);

  // 加载图片段落配置
  const fetchSegments = useCallback(async () => {
    try {
      const response = await fetch(staticFile(segmentsFile));
      const data: SegmentsConfig = await response.json();
      setSegments(data.segments);
      continueRender(handle);
    } catch (e) {
      console.error("Failed to load segments:", e);
      // 如果没有配置文件，使用默认的单张图片
      setSegments([
        {
          id: 1,
          startMs: 0,
          endMs: durationInFrames * (1000 / fps),
          topic: "默认",
          content: "",
          imageFile: "tech-illustration.jpg",
        },
      ]);
      continueRender(handle);
    }
  }, [handle, segmentsFile, durationInFrames, fps]);

  useEffect(() => {
    fetchCaptions();
    fetchSegments();
  }, [fetchCaptions, fetchSegments]);

  // 当前时间（毫秒）
  const currentTimeMs = (frame / fps) * 1000;

  // 获取当前应显示的图片段落
  const currentSegment = segments.find(
    (seg) => currentTimeMs >= seg.startMs && currentTimeMs < seg.endMs
  );

  // 获取当前字幕
  const currentCaption = captions.find(
    (c) => currentTimeMs >= c.startMs && currentTimeMs < c.endMs
  );

  return (
    <AbsoluteFill style={{ backgroundColor }}>
      {/* 渐变背景 */}
      <AbsoluteFill
        style={{
          background: `linear-gradient(180deg, ${backgroundColor} 0%, ${backgroundColor}ee 50%, ${backgroundColor}dd 100%)`,
        }}
      />

      {/* 技术图区域 - 根据段落切换 */}
      <AbsoluteFill
        style={{
          top: 40,
          height: 450,
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        {segments.map((segment, index) => {
          const segmentStartFrame = Math.round((segment.startMs / 1000) * fps);
          const segmentEndFrame = Math.round((segment.endMs / 1000) * fps);
          const segmentDuration = segmentEndFrame - segmentStartFrame;

          return (
            <Sequence
              key={segment.id}
              from={segmentStartFrame}
              durationInFrames={segmentDuration}
              premountFor={30}
            >
              <TechImage
                imageFile={segment.imageFile}
                topic={segment.topic}
                accentColor={accentColor}
              />
            </Sequence>
          );
        })}
      </AbsoluteFill>

      {/* 角色视频（透明 webm） */}
      <AbsoluteFill
        style={{
          top: "auto",
          bottom: 160,
          height: 650,
          justifyContent: "flex-end",
          alignItems: "center",
        }}
      >
        <Video
          src={staticFile(characterVideo)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
            objectPosition: "bottom center",
          }}
        />
      </AbsoluteFill>

      {/* 字幕区域 */}
      <AbsoluteFill
        style={{
          top: "auto",
          bottom: 50,
          height: 110,
          justifyContent: "center",
          alignItems: "center",
          padding: "0 35px",
        }}
      >
        {currentCaption && (
          <CaptionDisplay
            text={currentCaption.text}
            accentColor={accentColor}
          />
        )}
      </AbsoluteFill>

      {/* 装饰粒子 */}
      <FloatingParticles frame={frame} accentColor={accentColor} />
    </AbsoluteFill>
  );
};

// 技术图组件 - 带入场动画
const TechImage: React.FC<{
  imageFile: string;
  topic: string;
  accentColor: string;
}> = ({ imageFile, topic, accentColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 入场动画
  const scale = spring({
    frame,
    fps,
    config: {
      damping: 15,
      stiffness: 100,
    },
  });

  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  const slideY = interpolate(frame, [0, 20], [30, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        width: "92%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        transform: `scale(${scale}) translateY(${slideY}px)`,
        opacity,
      }}
    >
      {/* 图片 */}
      <Img
        src={staticFile(imageFile)}
        style={{
          width: "100%",
          maxWidth: 650,
          borderRadius: 12,
          boxShadow: "0 15px 50px rgba(0, 0, 0, 0.4)",
        }}
      />
      {/* 主题标签 */}
      {topic && (
        <div
          style={{
            marginTop: 12,
            padding: "6px 16px",
            backgroundColor: `${accentColor}22`,
            borderRadius: 20,
            fontSize: 18,
            fontWeight: "bold",
            color: accentColor,
            border: `1px solid ${accentColor}44`,
          }}
        >
          {topic}
        </div>
      )}
    </div>
  );
};

// 字幕显示组件
const CaptionDisplay: React.FC<{
  text: string;
  accentColor: string;
}> = ({ text, accentColor }) => {
  return (
    <div
      style={{
        fontSize: 30,
        fontWeight: "bold",
        textAlign: "center",
        lineHeight: 1.5,
        color: "#ffffff",
        textShadow: `0 2px 8px rgba(0, 0, 0, 0.9), 0 0 20px ${accentColor}33`,
        maxWidth: "100%",
        padding: "10px 18px",
        backgroundColor: "rgba(0, 0, 0, 0.55)",
        borderRadius: 10,
      }}
    >
      {text}
    </div>
  );
};

// 浮动粒子装饰
const FloatingParticles: React.FC<{
  frame: number;
  accentColor: string;
}> = ({ frame, accentColor }) => {
  const particles = [
    { x: 40, y: 280, size: 4, speed: 0.02, opacity: 0.25 },
    { x: 680, y: 350, size: 3, speed: 0.025, opacity: 0.2 },
    { x: 90, y: 550, size: 5, speed: 0.015, opacity: 0.3 },
    { x: 630, y: 650, size: 4, speed: 0.018, opacity: 0.25 },
    { x: 360, y: 180, size: 3, speed: 0.022, opacity: 0.15 },
  ];

  return (
    <>
      {particles.map((p, i) => {
        const yOffset = Math.sin(frame * p.speed) * 18;
        const xOffset = Math.cos(frame * p.speed * 0.7) * 8;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: p.x + xOffset,
              top: p.y + yOffset,
              width: p.size,
              height: p.size,
              borderRadius: "50%",
              backgroundColor: accentColor,
              opacity: p.opacity,
              boxShadow: `0 0 ${p.size * 2}px ${accentColor}`,
            }}
          />
        );
      })}
    </>
  );
};
