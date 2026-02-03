#!/usr/bin/env node
/**
 * Projects <-> Odyssey 同步脚本
 * 每晚 23:05 运行，检测卡片位置与代码目录是否一致
 */

import fs from 'fs';
import path from 'path';

const PROJECTS_ROOT = '/Users/liuyishou/usr/projects';
const ODYSSEY_ROOT = '/Users/liuyishou/usr/odyssey';

// 目录对应关系
const MAPPING = {
  'inbox': '0 收集箱/repo',
  'wip': '1 一切皆项目/wip',
  'polish': '1 一切皆项目/进行中',
  'published': '1 一切皆项目/已结项',
  'archive': '1 一切皆项目/搁置中',
};

// 反向映射
const REVERSE_MAPPING = Object.fromEntries(
  Object.entries(MAPPING).map(([k, v]) => [v, k])
);

function log(msg) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${msg}`);
}

function parseCardFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;

  const frontmatter = {};
  const lines = match[1].split('\n');
  let currentKey = null;

  for (const line of lines) {
    const keyMatch = line.match(/^(\w+):\s*(.*)$/);
    if (keyMatch) {
      currentKey = keyMatch[1];
      const value = keyMatch[2].trim();
      if (value.startsWith('[') || value === '') {
        frontmatter[currentKey] = [];
      } else {
        frontmatter[currentKey] = value;
      }
    } else if (currentKey && line.match(/^\s+-\s+/)) {
      const item = line.replace(/^\s+-\s+/, '').trim();
      if (Array.isArray(frontmatter[currentKey])) {
        frontmatter[currentKey].push(item);
      }
    }
  }

  return frontmatter;
}

function updateCardPath(cardPath, newPath, newStatus) {
  let content = fs.readFileSync(cardPath, 'utf-8');
  content = content.replace(/path:\s*.+/, `path: ${newPath}`);
  content = content.replace(/status:\s*.+/, `status: ${newStatus}`);
  fs.writeFileSync(cardPath, content);
}

function findAllCards() {
  const cards = [];

  for (const [projDir, odysseyDir] of Object.entries(MAPPING)) {
    const odysseyPath = path.join(ODYSSEY_ROOT, odysseyDir);
    if (!fs.existsSync(odysseyPath)) continue;

    const files = fs.readdirSync(odysseyPath);
    for (const file of files) {
      if (!file.endsWith('.md')) continue;

      const cardPath = path.join(odysseyPath, file);
      const content = fs.readFileSync(cardPath, 'utf-8');
      const frontmatter = parseCardFrontmatter(content);

      if (frontmatter?.type === 'code-project' && frontmatter?.path) {
        cards.push({
          cardPath,
          cardDir: odysseyDir,
          expectedProjDir: projDir,
          codePath: frontmatter.path,
          status: frontmatter.status,
          name: file.replace(/\$?\.md$/, ''),
        });
      }
    }
  }

  return cards;
}

function sync() {
  log('开始同步 projects <-> odyssey（以 Obsidian 卡片为准）');

  const cards = findAllCards();
  let syncCount = 0;

  for (const card of cards) {
    const actualCodePath = card.codePath;

    if (!fs.existsSync(actualCodePath)) {
      log(`[警告] 代码目录不存在: ${actualCodePath}`);
      continue;
    }

    // 从 codePath 解析出代码当前所在的 projects 子目录
    const projMatch = actualCodePath.match(/\/projects\/(\w+)\//);
    if (!projMatch) continue;

    const actualProjDir = projMatch[1];

    // 卡片所在的 odyssey 目录对应的 projects 目录
    const expectedProjDir = card.expectedProjDir;

    // 如果代码位置和卡片位置不一致，以卡片为准，移动代码
    if (actualProjDir !== expectedProjDir) {
      log(`[同步] ${card.name}: 卡片在 ${expectedProjDir}, 代码在 ${actualProjDir}`);

      // 计算代码应该移动到的新路径
      const projectName = path.basename(actualCodePath);
      const newCodePath = path.join(PROJECTS_ROOT, expectedProjDir, projectName);

      // 确保目标目录存在
      const targetDir = path.join(PROJECTS_ROOT, expectedProjDir);
      if (!fs.existsSync(targetDir)) {
        fs.mkdirSync(targetDir, { recursive: true });
      }

      // 移动代码目录
      fs.renameSync(actualCodePath, newCodePath);
      log(`[移动代码] ${actualCodePath} -> ${newCodePath}`);

      // 更新卡片的 path 和 status
      updateCardPath(card.cardPath, newCodePath, expectedProjDir);
      log(`[更新卡片] path: ${newCodePath}, status: ${expectedProjDir}`);

      syncCount++;
    }
  }

  // 检查是否有代码项目没有卡片
  for (const projDir of ['inbox', 'wip', 'polish', 'published']) {
    const projPath = path.join(PROJECTS_ROOT, projDir);
    if (!fs.existsSync(projPath)) continue;

    const projects = fs.readdirSync(projPath).filter(f => {
      const fullPath = path.join(projPath, f);
      return fs.statSync(fullPath).isDirectory() && !f.startsWith('.');
    });

    for (const proj of projects) {
      const hasCard = cards.some(c => c.codePath.includes(`/${projDir}/${proj}`));
      if (!hasCard) {
        log(`[提示] ${projDir}/${proj} 没有 odyssey 卡片`);
      }
    }
  }

  log(`同步完成，处理了 ${syncCount} 个变更`);
}

sync();
