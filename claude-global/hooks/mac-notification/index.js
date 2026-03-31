#!/usr/bin/env node
/**
 * Mac Notification Hook (Notification)
 * 当 Claude Code 发送通知时，同步发送 macOS 系统通知
 */

const { execSync } = require('child_process');

// 从 stdin 读取输入
async function readInput() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('readable', () => {
      let chunk;
      while ((chunk = process.stdin.read()) !== null) {
        data += chunk;
      }
    });
    process.stdin.on('end', () => {
      try {
        resolve(JSON.parse(data));
      } catch (e) {
        resolve({ message: data });
      }
    });
  });
}

function sendMacNotification(title, message) {
  // 转义单引号
  const safeTitle = (title || 'Claude Code').replace(/'/g, "'\"'\"'");
  const safeMessage = (message || '').replace(/'/g, "'\"'\"'");

  try {
    execSync(`osascript -e 'display notification "${safeMessage}" with title "${safeTitle}" sound name "Glass"'`, {
      timeout: 5000
    });
    return true;
  } catch (e) {
    console.error('通知发送失败:', e.message);
    return false;
  }
}

async function main() {
  const input = await readInput();

  // Claude Code 通知格式
  const title = input.title || 'Claude Code';
  const message = input.message || input.body || input.content || '';

  if (message) {
    sendMacNotification(title, message);
  }

  console.log(JSON.stringify({ result: 'success' }));
}

main().catch(console.error);
