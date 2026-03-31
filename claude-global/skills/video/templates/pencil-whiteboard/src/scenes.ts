/**
 * 场景配置文件
 *
 * 每个场景包含：
 * - slide: 图片路径（相对于 public 目录）
 * - audio: 配音路径（相对于 public 目录）
 * - duration: 场景时长（秒）= 绘制时间(1.5s) + 配音时长 + 缓冲(0.5s)
 */

export interface Scene {
  slide: string;
  audio: string;
  duration: number;
}

export const scenes: Scene[] = [
  // 示例配置，根据实际内容修改
  { slide: "slides/01_hook.jpg", audio: "audio/hook.mp3", duration: 7.5 },
  { slide: "slides/02_scene1.png", audio: "audio/scene1.mp3", duration: 8 },
  { slide: "slides/03_scene2.png", audio: "audio/scene2.mp3", duration: 8 },
  { slide: "slides/04_outro.jpg", audio: "audio/outro.mp3", duration: 8 },
];

// 计算总时长（帧数）- 用于 Root.tsx
export const totalDuration = scenes.reduce((sum, scene) => sum + scene.duration, 0);
