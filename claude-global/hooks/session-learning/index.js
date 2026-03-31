#!/usr/bin/env node
/**
 * Session Learning Hook (SessionEnd)
 * 会话结束时自动提取可复用的 patterns
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

const CONFIG = {
  PATTERNS_DIR: path.join(process.env.HOME, '.claude', 'learned-patterns'),
  OPENROUTER_API_KEY: process.env.OPENROUTER_API_KEY,
  OPENROUTER_MODEL: 'google/gemini-3-pro-preview'
};

// 确保目录存在
if (!fs.existsSync(CONFIG.PATTERNS_DIR)) {
  fs.mkdirSync(CONFIG.PATTERNS_DIR, { recursive: true });
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

// 调用 OpenRouter 分析会话
async function analyzeSession(sessionSummary) {
  if (!CONFIG.OPENROUTER_API_KEY) {
    return null;
  }

  return new Promise((resolve) => {
    const prompt = `分析以下 Claude Code 会话摘要，提取可复用的模式或经验。

会话摘要：
${sessionSummary}

如果发现有价值的模式，返回 JSON：
{
  "hasPattern": true,
  "patternName": "模式名称（英文，如 react-form-validation）",
  "description": "简短描述",
  "keyInsights": ["要点1", "要点2"],
  "codeSnippet": "如果有，关键代码片段"
}

如果没有值得记录的模式：
{ "hasPattern": false }

只返回 JSON。`;

    const requestData = JSON.stringify({
      model: CONFIG.OPENROUTER_MODEL,
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 500
    });

    const options = {
      hostname: 'openrouter.ai',
      port: 443,
      path: '/api/v1/chat/completions',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${CONFIG.OPENROUTER_API_KEY}`,
        'Content-Length': Buffer.byteLength(requestData)
      }
    };

    const req = https.request(options, (res) => {
      let responseData = '';
      res.on('data', (chunk) => responseData += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(responseData);
          const text = parsed.choices?.[0]?.message?.content || '';
          const jsonMatch = text.match(/\{[\s\S]*\}/);
          if (jsonMatch) {
            resolve(JSON.parse(jsonMatch[0]));
          } else {
            resolve(null);
          }
        } catch (e) {
          resolve(null);
        }
      });
    });

    req.on('error', () => resolve(null));
    req.setTimeout(10000, () => {
      req.destroy();
      resolve(null);
    });

    req.write(requestData);
    req.end();
  });
}

async function main() {
  const input = await readInput();

  // 获取会话摘要（如果有）
  const sessionSummary = input.session_summary || input.summary || '';

  if (!sessionSummary || sessionSummary.length < 100) {
    console.log(JSON.stringify({ result: 'skipped', reason: 'Session too short' }));
    return;
  }

  try {
    const analysis = await analyzeSession(sessionSummary);

    if (analysis && analysis.hasPattern) {
      // 保存模式到文件
      const fileName = `${analysis.patternName || 'pattern'}-${Date.now()}.md`;
      const filePath = path.join(CONFIG.PATTERNS_DIR, fileName);

      const content = `# ${analysis.patternName}

${analysis.description}

## 要点

${analysis.keyInsights.map(i => `- ${i}`).join('\n')}

${analysis.codeSnippet ? `## 代码示例\n\n\`\`\`\n${analysis.codeSnippet}\n\`\`\`` : ''}

---
*自动提取于 ${new Date().toLocaleString('zh-CN')}*
`;

      fs.writeFileSync(filePath, content, 'utf8');

      console.log(JSON.stringify({
        result: 'success',
        message: `已提取模式: ${analysis.patternName}`
      }));
    } else {
      console.log(JSON.stringify({ result: 'success', message: 'No patterns extracted' }));
    }
  } catch (error) {
    console.log(JSON.stringify({ result: 'error', message: error.message }));
  }
}

main().catch(console.error);
