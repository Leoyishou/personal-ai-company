#!/usr/bin/env node
/**
 * TypeScript Type Check Hook (PostToolUse)
 * 编辑 TS/TSX 文件后自动运行类型检查
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

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

function findTsConfig(startDir) {
  let currentDir = startDir;
  while (currentDir !== '/') {
    const tsConfigPath = path.join(currentDir, 'tsconfig.json');
    if (fs.existsSync(tsConfigPath)) {
      return currentDir;
    }
    currentDir = path.dirname(currentDir);
  }
  return null;
}

async function main() {
  const input = await readInput();

  // 获取编辑的文件路径
  const toolInput = input.tool_input || {};
  const filePath = toolInput.file_path || '';

  // 只检查 TS/TSX 文件
  if (!filePath.match(/\.(ts|tsx)$/)) {
    console.log(JSON.stringify({ result: 'skipped', reason: 'Not a TypeScript file' }));
    return;
  }

  // 找到项目根目录（有 tsconfig.json 的地方）
  const projectRoot = findTsConfig(path.dirname(filePath));

  if (!projectRoot) {
    console.log(JSON.stringify({ result: 'skipped', reason: 'No tsconfig.json found' }));
    return;
  }

  try {
    // 运行 tsc --noEmit 只做类型检查
    execSync('npx tsc --noEmit 2>&1', {
      cwd: projectRoot,
      timeout: 30000,
      encoding: 'utf8'
    });

    console.log(JSON.stringify({
      result: 'success',
      message: 'TypeScript 类型检查通过'
    }));
  } catch (error) {
    // 类型检查失败，输出警告
    const output = error.stdout || error.message;
    const lines = output.split('\n').slice(0, 10).join('\n'); // 只取前 10 行

    console.log(JSON.stringify({
      result: 'warning',
      message: `TypeScript 类型错误:\n${lines}`
    }));
  }
}

main().catch(console.error);
