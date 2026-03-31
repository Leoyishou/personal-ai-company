import React from 'react';
import { Composition } from 'remotion';
import { StickmanVideo } from './StickmanVideo';

// Default props for preview
const defaultProps = {
  title: '火柴人视频示例',
  segments: [
    {
      id: 1,
      text: '这是第一段解说词示例',
      duration: 4,
      audio: null,
      image: 'https://via.placeholder.com/800x600/ffffff/000000?text=Frame+1',
    },
    {
      id: 2,
      text: '这是第二段解说词示例',
      duration: 4,
      audio: null,
      image: 'https://via.placeholder.com/800x600/ffffff/000000?text=Frame+2',
    },
    {
      id: 3,
      text: '这是第三段解说词示例',
      duration: 4,
      audio: null,
      image: 'https://via.placeholder.com/800x600/ffffff/000000?text=Frame+3',
    },
  ],
  bgm: null,
};

// Calculate total duration
const calculateDuration = (segments: typeof defaultProps.segments, fps: number) => {
  return segments.reduce((total, segment) => total + segment.duration * fps, 0);
};

export const RemotionRoot: React.FC = () => {
  const fps = 30;
  const durationInFrames = calculateDuration(defaultProps.segments, fps);

  return (
    <>
      <Composition
        id="StickmanVideo"
        component={StickmanVideo}
        durationInFrames={durationInFrames}
        fps={fps}
        width={960}
        height={720}
        defaultProps={defaultProps}
      />
    </>
  );
};
