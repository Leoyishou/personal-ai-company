#!/usr/bin/env node
/**
 * Pre-Compact Hook (PreCompact)
 * 压缩前保存关键上下文到文件，防止信息丢失
 */

const fs = require('fs');
const path = require('path');

const CONFIG = {
  CONTEXT_DIR: path.join(process.env.HOME, '.claude', 'saved-contexts'),
  MAX_FILES: 20  // 最多保留的上下文文件数
};

// 确保目录存在
if (!fs.existsSync(CONFIG.CONTEXT_DIR)) {
  fs.mkdirSync(CONFIG.CONTEXT_DIR, { recursive: true });
}

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

// 清理旧文件
function cleanupOldFiles() {
  const files = fs.readdirSync(CONFIG.CONTEXT_DIR)
    .filter(f => f.endsWith('.md'))
    .map(f => ({
      name: f,
      path: path.join(CONFIG.CONTEXT_DIR, f),
      time: fs.statSync(path.join(CONFIG.CONTEXT_DIR, f)).mtime
    }))
    .sort((a, b) => b.time - a.time);

  // 删除超出限制的旧文件
  files.slice(CONFIG.MAX_FILES).forEach(f => {
    try {
      fs.unlinkSync(f.path);
    } catch (e) {
      // ignore
    }
  });
}

async function main() {
  const input = await readInput();

  // 获取要压缩的上下文
  const contextToCompact = input.context || input.messages || '';
  const sessionId = input.session_id || process.env.CLAUDE_SESSION_ID || 'unknown';
  const workingDir = input.working_directory || process.env.CLAUDE_WORKING_DIRECTORY || process.cwd();

  if (!contextToCompact || contextToCompact.length < 500) {
    console.log(JSON.stringify({ result: 'skipped', reason: 'Context too short' }));
    return;
  }

  try {
    // 清理旧文件
    cleanupOldFiles();

    // 生成文件名
    const now = new Date();
    const timestamp = now.toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const projectName = path.basename(workingDir);
    const fileName = `${timestamp}_${projectName}.md`;
    const filePath = path.join(CONFIG.CONTEXT_DIR, fileName);

    // 提取关键信息
    const content = `# 会话上下文备份

| 项目 | 值 |
|------|-----|
| 时间 | ${now.toLocaleString('zh-CN')} |
| 项目 | ${projectName} |
| 会话 | ${sessionId} |

## 上下文摘要

${typeof contextToCompact === 'string'
  ? contextToCompact.substring(0, 5000)
  : JSON.stringify(contextToCompact, null, 2).substring(0, 5000)}

---
*由 PreCompact Hook 自动保存*
`;

    fs.writeFileSync(filePath, content, 'utf8');

    console.log(JSON.stringify({
      result: 'success',
      message: `上下文已保存: ${fileName}`
    }));
  } catch (error) {
    console.log(JSON.stringify({ result: 'error', message: error.message }));
  }
}

main().catch(console.error);
