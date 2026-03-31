import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from 'remotion';

// Segment data structure
interface Segment {
  id: number;
  text: string;
  duration: number;
  audio: string | null;
  image: string;
}

// Video configuration
interface StickmanVideoProps {
  segments: Segment[];
  bgm: string | null;
  title: string;
}

// Subtitle component with animation
const Subtitle: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame, [0, fps * 0.3], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 40,
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '0 40px',
      }}
    >
      <div
        style={{
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          padding: '16px 32px',
          borderRadius: 8,
          opacity,
        }}
      >
        <span
          style={{
            fontSize: 36,
            fontWeight: 'bold',
            color: '#333',
            fontFamily: 'Microsoft YaHei, PingFang SC, sans-serif',
            textAlign: 'center',
            display: 'block',
          }}
        >
          {text}
        </span>
      </div>
    </div>
  );
};

// Single segment component
const SegmentScene: React.FC<{ segment: Segment }> = ({ segment }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Image entrance animation
  const scale = spring({
    frame,
    fps,
    config: {
      damping: 100,
      stiffness: 200,
    },
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#f8f8f8',
      }}
    >
      {/* Stickman illustration */}
      <div
        style={{
          position: 'absolute',
          top: 40,
          left: 0,
          right: 0,
          bottom: 120,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          transform: `scale(${scale})`,
        }}
      >
        <Img
          src={segment.image}
          style={{
            maxWidth: '80%',
            maxHeight: '100%',
            objectFit: 'contain',
          }}
        />
      </div>

      {/* Subtitle */}
      <Subtitle text={segment.text} />

      {/* Segment audio */}
      {segment.audio && (
        <Audio src={segment.audio} volume={1} />
      )}
    </AbsoluteFill>
  );
};

// Header bar component
const HeaderBar: React.FC<{ title: string }> = ({ title }) => {
  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: 40,
        backgroundColor: 'rgba(200, 200, 200, 0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px',
        zIndex: 100,
      }}
    >
      <span
        style={{
          fontSize: 14,
          color: '#666',
          fontFamily: 'Microsoft YaHei, sans-serif',
        }}
      >
        {title}
      </span>
      <span
        style={{
          fontSize: 12,
          color: '#999',
        }}
      >
        个人观点，无不良引导
      </span>
    </div>
  );
};

// Main video composition
export const StickmanVideo: React.FC<StickmanVideoProps> = ({
  segments,
  bgm,
  title,
}) => {
  const { fps } = useVideoConfig();

  // Calculate frame positions for each segment
  let currentFrame = 0;
  const segmentFrames = segments.map((segment) => {
    const startFrame = currentFrame;
    const durationFrames = segment.duration * fps;
    currentFrame += durationFrames;
    return { segment, startFrame, durationFrames };
  });

  return (
    <AbsoluteFill style={{ backgroundColor: '#f8f8f8' }}>
      {/* Header */}
      <HeaderBar title={title} />

      {/* Segment sequences */}
      {segmentFrames.map(({ segment, startFrame, durationFrames }) => (
        <Sequence
          key={segment.id}
          from={startFrame}
          durationInFrames={durationFrames}
        >
          <SegmentScene segment={segment} />
        </Sequence>
      ))}

      {/* Background music */}
      {bgm && (
        <Audio src={bgm} volume={0.3} />
      )}
    </AbsoluteFill>
  );
};

export default StickmanVideo;
