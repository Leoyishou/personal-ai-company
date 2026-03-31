#!/usr/bin/env node
/**
 * Console.log Check Hook (PostToolUse)
 * 检测新增的 console.log 语句并提醒
 */

const fs = require('fs');
const path = require('path');

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

async function main() {
  const input = await readInput();

  // 获取编辑的文件和新内容
  const toolInput = input.tool_input || {};
  const filePath = toolInput.file_path || '';
  const newString = toolInput.new_string || toolInput.content || '';

  // 只检查 JS/TS 文件
  if (!filePath.match(/\.(js|jsx|ts|tsx)$/)) {
    console.log(JSON.stringify({ result: 'skipped' }));
    return;
  }

  // 检查新增内容是否包含 console.log
  const consoleMatches = newString.match(/console\.(log|debug|info)\(/g);

  if (consoleMatches && consoleMatches.length > 0) {
    console.log(JSON.stringify({
      result: 'warning',
      message: `检测到 ${consoleMatches.length} 个 console 语句，记得提交前清理`
    }));
  } else {
    console.log(JSON.stringify({ result: 'success' }));
  }
}

main().catch(console.error);
