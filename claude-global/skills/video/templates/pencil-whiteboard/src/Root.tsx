import { Composition } from "remotion";
import { PencilWhiteboardComposition } from "./PencilWhiteboard";
import { totalDuration } from "./scenes";

export const RemotionRoot: React.FC = () => {
  const fps = 30;
  const durationInFrames = Math.round(totalDuration * fps) + 100; // 额外缓冲

  return (
    <>
      <Composition
        id="Main"
        component={PencilWhiteboardComposition}
        durationInFrames={durationInFrames}
        fps={fps}
        width={1080}
        height={1920}
      />
    </>
  );
};
