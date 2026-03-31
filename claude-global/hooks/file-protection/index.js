#!/usr/bin/env node
/**
 * File Protection Hook (PreToolUse)
 * 阻止修改敏感文件，如 .env、lock 文件等
 */

const fs = require('fs');
const path = require('path');

// 受保护的文件模式
const PROTECTED_PATTERNS = [
  /^\.env(\..*)?$/,           // .env, .env.local, .env.production
  /^package-lock\.json$/,
  /^pnpm-lock\.yaml$/,
  /^yarn\.lock$/,
  /^bun\.lockb$/,
  /\.pem$/,
  /\.key$/,
  /^credentials\./,
  /^secrets\./,
  /^\.claude\/secrets\.env$/
];

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
        resolve({});
      }
    });
  });
}

function isProtectedFile(filePath) {
  if (!filePath) return false;
  const fileName = path.basename(filePath);
  const relativePath = filePath.replace(process.env.HOME, '');

  return PROTECTED_PATTERNS.some(pattern =>
    pattern.test(fileName) || pattern.test(relativePath)
  );
}

async function main() {
  const input = await readInput();

  // 获取工具输入中的文件路径
  const toolInput = input.tool_input || {};
  const filePath = toolInput.file_path || toolInput.path || '';

  if (isProtectedFile(filePath)) {
    // 阻止操作
    console.log(JSON.stringify({
      decision: 'block',
      reason: `受保护的文件: ${path.basename(filePath)}。如需修改请明确确认。`
    }));
  } else {
    // 允许操作
    console.log(JSON.stringify({ decision: 'allow' }));
  }
}

main().catch(console.error);
