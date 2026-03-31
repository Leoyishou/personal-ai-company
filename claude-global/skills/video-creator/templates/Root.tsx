import { Composition } from "remotion";
import { VideoComposition } from "./VideoComposition";

// 配置参数 - 根据实际视频调整
const CONFIG = {
  durationInFrames: 475,  // 视频总帧数 (时长秒数 * fps)
  fps: 30,                // 帧率
  width: 720,             // 宽度 (竖屏)
  height: 1280,           // 高度 (竖屏)
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="MainVideo"
      component={VideoComposition}
      durationInFrames={CONFIG.durationInFrames}
      fps={CONFIG.fps}
      width={CONFIG.width}
      height={CONFIG.height}
      defaultProps={{
        characterVideo: "character.webm",
        techIllustration: "tech-illustration.jpg",
        subtitlesFile: "subtitles.srt",
        backgroundColor: "#1a1a2e",
        accentColor: "#00d4ff",
      }}
    />
  );
};
