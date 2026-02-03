import { Hono } from "hono";
import { serveStatic } from "hono/bun";
import { cors } from "hono/cors";
import { execSync, spawn } from "child_process";
import { mkdir, writeFile, readdir, unlink, stat } from "fs/promises";
import { join } from "path";
import { existsSync } from "fs";

const app = new Hono();
const PORT = 3456;

// 存储目录
const UPLOAD_DIR = join(process.env.HOME!, "Videos", "instant-publish");
const PROCESSED_DIR = join(UPLOAD_DIR, "processed");
const LOGS_DIR = join(UPLOAD_DIR, "logs");

// 确保目录存在
await mkdir(UPLOAD_DIR, { recursive: true });
await mkdir(PROCESSED_DIR, { recursive: true });
await mkdir(LOGS_DIR, { recursive: true });

app.use("*", cors());

// 静态文件
app.use("/", serveStatic({ root: "./public" }));
app.use("/assets/*", serveStatic({ root: "./public" }));

// 上传视频
app.post("/api/upload", async (c) => {
  try {
    const formData = await c.req.formData();
    const video = formData.get("video") as File;
    const title = formData.get("title") as string;
    const platforms = formData.get("platforms") as string; // "bilibili,xiaohongshu"
    const burnSubtitle = formData.get("burnSubtitle") === "true";
    const testMode = formData.get("testMode") === "true";

    if (!video || !title) {
      return c.json({ error: "缺少视频或标题" }, 400);
    }

    // 生成文件名
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
    const safeTitle = title.replace(/[\/\\:*?"<>|]/g, "_").slice(0, 50);
    const webmFilename = `${timestamp}_${safeTitle}.webm`;
    const webmPath = join(UPLOAD_DIR, webmFilename);
    const filename = `${timestamp}_${safeTitle}.mp4`;
    const filepath = join(UPLOAD_DIR, filename);

    // 保存原始 webm 视频
    const buffer = await video.arrayBuffer();
    await writeFile(webmPath, Buffer.from(buffer));

    console.log(`[上传] ${filename} (${(buffer.byteLength / 1024 / 1024).toFixed(1)}MB)`);

    // 创建任务元数据
    const meta = {
      title,
      platforms: platforms?.split(",").filter(Boolean) || ["bilibili"],
      burnSubtitle,
      testMode,
      webmPath,
      filepath,
      createdAt: new Date().toISOString(),
      status: "pending",
    };

    const metaPath = filepath.replace(".mp4", ".json");
    await writeFile(metaPath, JSON.stringify(meta, null, 2));

    // 异步触发处理流程
    processVideo(webmPath, filepath, meta).catch(console.error);

    return c.json({
      success: true,
      message: "视频已上传，正在处理...",
      taskId: filename,
    });
  } catch (err) {
    console.error("上传失败:", err);
    return c.json({ error: String(err) }, 500);
  }
});

// 查询任务状态
app.get("/api/status/:taskId", async (c) => {
  const taskId = c.req.param("taskId");
  const metaPath = join(UPLOAD_DIR, taskId.replace(".mp4", ".json"));

  if (!existsSync(metaPath)) {
    return c.json({ error: "任务不存在" }, 404);
  }

  const meta = JSON.parse(await Bun.file(metaPath).text());
  return c.json(meta);
});

// 列出最近任务
app.get("/api/tasks", async (c) => {
  const files = await readdir(UPLOAD_DIR);
  const tasks = [];

  for (const file of files) {
    if (file.endsWith(".json") && !file.startsWith(".")) {
      const metaPath = join(UPLOAD_DIR, file);
      const meta = JSON.parse(await Bun.file(metaPath).text());
      tasks.push({
        id: file.replace(".json", ".mp4"),
        ...meta,
      });
    }
  }

  // 按时间倒序
  tasks.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  return c.json(tasks.slice(0, 20));
});

// 处理视频
async function processVideo(webmPath: string, mp4Path: string, meta: any) {
  const logPath = join(LOGS_DIR, `${Date.now()}.log`);
  const log = (msg: string) => {
    console.log(msg);
    Bun.write(logPath, `${new Date().toISOString()} ${msg}\n`, { append: true });
  };

  const updateMeta = async (update: Partial<typeof meta>) => {
    Object.assign(meta, update);
    const metaPath = mp4Path.replace(".mp4", ".json");
    await writeFile(metaPath, JSON.stringify(meta, null, 2));
  };

  try {
    await updateMeta({ status: "processing" });
    log(`[开始处理] ${meta.title}`);

    // 0. WebM 转 MP4
    log("[0/5] WebM 转 MP4...");
    try {
      execSync(
        `ffmpeg -y -i "${webmPath}" -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k "${mp4Path}"`,
        { stdio: "inherit", timeout: 600000 }
      );
      log(`[转码] 完成: ${mp4Path}`);
    } catch (err) {
      log(`[转码] 失败: ${err}`);
      throw new Error("视频转码失败");
    }

    const filepath = mp4Path;

    // 1. ASR 生成字幕
    log("[1/5] ASR 语音识别...");
    const srtPath = filepath.replace(".mp4", ".srt");

    try {
      execSync(
        `ALL_PROXY="" HTTP_PROXY="" HTTPS_PROXY="" NO_PROXY="*" python3 ~/.claude/skills/speech-recognition/scripts/speech_recognition.py -i "${filepath}" -o "${srtPath}" -f srt -m segment`,
        { stdio: "inherit", timeout: 600000 }
      );
      await updateMeta({ srtPath });
      log(`[ASR] 完成: ${srtPath}`);
    } catch (err) {
      log(`[ASR] 失败: ${err}`);
    }

    // 2. 生成封面（截取第 1 秒的帧）
    log("[2/5] 生成封面...");
    const coverPath = filepath.replace(".mp4", "_cover.jpg");
    try {
      execSync(
        `ffmpeg -y -i "${filepath}" -ss 00:00:01 -vframes 1 -q:v 2 "${coverPath}"`,
        { stdio: "inherit" }
      );
      await updateMeta({ coverPath });
      log(`[封面] 完成: ${coverPath}`);
    } catch (err) {
      log(`[封面] 失败: ${err}`);
    }

    // 3. (可选) 烧录字幕
    let finalVideoPath = filepath;
    if (meta.burnSubtitle && existsSync(srtPath)) {
      log("[3/5] 烧录字幕...");
      const burnedPath = filepath.replace(".mp4", "_subtitled.mp4");
      try {
        execSync(
          `ffmpeg -y -i "${filepath}" -vf "subtitles='${srtPath}':force_style='FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2'" -c:a copy "${burnedPath}"`,
          { stdio: "inherit", timeout: 600000 }
        );
        finalVideoPath = burnedPath;
        await updateMeta({ burnedVideoPath: burnedPath });
        log(`[字幕烧录] 完成: ${burnedPath}`);
      } catch (err) {
        log(`[字幕烧录] 失败: ${err}`);
      }
    } else {
      log("[3/5] 跳过字幕烧录");
    }

    // 4. 发布到平台
    log("[4/5] 发布到平台...");
    const results: Record<string, string> = {};

    if (meta.testMode) {
      log("[测试模式] 跳过实际发布");
      results.testMode = "skipped";
    } else {
      for (const platform of meta.platforms) {
        if (platform === "bilibili") {
          log(`[发布] B站...`);
          try {
            const cmd = `cd ~/.claude/skills/biliup-publish && biliup upload "${finalVideoPath}" --title "${meta.title}" --desc "由 Instant Video Publisher 自动发布" --tag "科技,分享" --tid 231 --copyright 1`;
            execSync(cmd, { stdio: "inherit", timeout: 300000 });
            results.bilibili = "success";
            log(`[B站] 发布成功`);
          } catch (err) {
            results.bilibili = `failed: ${err}`;
            log(`[B站] 发布失败: ${err}`);
          }
        }

        if (platform === "xiaohongshu") {
          log(`[发布] 小红书...`);
          try {
            const cmd = `python3 ~/.claude/skills/xiaohongshu/scripts/xhs_publish.py video --title "${meta.title.slice(0, 20)}" --content "${meta.title}" --tags "分享,日常" --video "${finalVideoPath}"`;
            execSync(cmd, { stdio: "inherit", timeout: 300000 });
            results.xiaohongshu = "success";
            log(`[小红书] 发布成功`);
          } catch (err) {
            results.xiaohongshu = `failed: ${err}`;
            log(`[小红书] 发布失败: ${err}`);
          }
        }
      }
    }

    await updateMeta({
      status: "completed",
      results,
      completedAt: new Date().toISOString(),
    });

    log(`[完成] ${meta.title}`);

    // 发送通知
    try {
      execSync(`osascript -e 'display notification "视频已发布完成" with title "Instant Publisher" sound name "Glass"'`);
    } catch {}

  } catch (err) {
    log(`[错误] ${err}`);
    await updateMeta({ status: "failed", error: String(err) });
  }
}

console.log(`
╔═══════════════════════════════════════════════════╗
║          Instant Video Publisher v1.0             ║
║                                                   ║
║  录制页面: http://localhost:${PORT}                 ║
║  手机访问: http://<你的IP>:${PORT}                   ║
║                                                   ║
║  视频存储: ${UPLOAD_DIR}
╚═══════════════════════════════════════════════════╝
`);

export default {
  port: PORT,
  fetch: app.fetch,
};
