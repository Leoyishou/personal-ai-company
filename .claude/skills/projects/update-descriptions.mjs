#!/usr/bin/env node
/**
 * 项目描述自动提取与更新
 * 从 README.md、package.json、pyproject.toml 等提取一句话描述
 *
 * 用法：node update-descriptions.mjs [--ai]
 * --ai: 对没有描述的项目使用 AI 生成描述（需要 OPENROUTER_API_KEY）
 */

import fs from 'fs';
import path from 'path';

const PROJECTS_ROOT = '/Users/liuyishou/usr/projects';
const METADATA_PATH = '/Users/liuyishou/.claude/skills/projects/metadata.json';
const DIRS = ['wip', 'polish', 'inbox', 'published', 'archive'];

function loadMetadata() {
  try {
    return JSON.parse(fs.readFileSync(METADATA_PATH, 'utf-8'));
  } catch {
    return {};
  }
}

function saveMetadata(metadata) {
  fs.writeFileSync(METADATA_PATH, JSON.stringify(metadata, null, 2));
}

function extractFromReadme(projectPath) {
  const readmePaths = ['README.md', 'readme.md', 'Readme.md', 'README'];

  for (const readme of readmePaths) {
    const readmePath = path.join(projectPath, readme);
    if (fs.existsSync(readmePath)) {
      const content = fs.readFileSync(readmePath, 'utf-8');
      const lines = content.split('\n').filter(l => l.trim());

      // 跳过标题行，找第一行有意义的描述
      for (const line of lines) {
        const trimmed = line.trim();
        // 跳过标题、徽章、空行
        if (trimmed.startsWith('#')) continue;
        if (trimmed.startsWith('![')) continue;
        if (trimmed.startsWith('[!')) continue;
        if (trimmed.startsWith('<!--')) continue;
        if (trimmed.length < 10) continue;

        // 清理 markdown 链接
        let desc = trimmed.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
        // 截断到一句话
        desc = desc.split(/[。.!！?？]/)[0];
        if (desc.length > 100) desc = desc.slice(0, 100) + '...';
        return desc;
      }
    }
  }
  return null;
}

function extractFromPackageJson(projectPath) {
  const pkgPath = path.join(projectPath, 'package.json');
  if (fs.existsSync(pkgPath)) {
    try {
      const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
      if (pkg.description && pkg.description.length > 5) {
        return pkg.description;
      }
    } catch {}
  }
  return null;
}

function extractFromPyproject(projectPath) {
  const pyprojectPath = path.join(projectPath, 'pyproject.toml');
  if (fs.existsSync(pyprojectPath)) {
    const content = fs.readFileSync(pyprojectPath, 'utf-8');
    const match = content.match(/description\s*=\s*["']([^"']+)["']/);
    if (match) return match[1];
  }
  return null;
}

function extractFromCargoToml(projectPath) {
  const cargoPath = path.join(projectPath, 'Cargo.toml');
  if (fs.existsSync(cargoPath)) {
    const content = fs.readFileSync(cargoPath, 'utf-8');
    const match = content.match(/description\s*=\s*["']([^"']+)["']/);
    if (match) return match[1];
  }
  return null;
}

function guessFromStructure(projectPath) {
  const files = fs.readdirSync(projectPath);

  // 基于文件结构猜测项目类型
  if (files.includes('app.json') || files.includes('expo-env.d.ts')) {
    return 'Expo/React Native 应用';
  }
  if (files.includes('next.config.js') || files.includes('next.config.ts')) {
    return 'Next.js 应用';
  }
  if (files.includes('vite.config.ts') || files.includes('vite.config.js')) {
    return 'Vite 前端项目';
  }
  if (files.includes('Cargo.toml')) {
    return 'Rust 项目';
  }
  if (files.includes('go.mod')) {
    return 'Go 项目';
  }
  if (files.includes('requirements.txt') || files.includes('pyproject.toml')) {
    return 'Python 项目';
  }
  if (files.includes('SKILL.md')) {
    return 'Claude Code Skill';
  }
  if (files.includes('Dockerfile') || files.includes('docker-compose.yml')) {
    return 'Docker 容器化项目';
  }

  return null;
}

function extractDescription(projectPath) {
  // 优先级：package.json > README > pyproject > cargo > 结构猜测
  return extractFromPackageJson(projectPath)
    || extractFromReadme(projectPath)
    || extractFromPyproject(projectPath)
    || extractFromCargoToml(projectPath)
    || guessFromStructure(projectPath);
}

import { execSync } from 'child_process';

function getLastCommitDate(projectPath) {
  const gitDir = path.join(projectPath, '.git');
  if (!fs.existsSync(gitDir)) return null;

  try {
    const result = execSync('git log -1 --format=%ci', {
      cwd: projectPath,
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe']
    });
    return result.trim().split(' ')[0]; // YYYY-MM-DD
  } catch {
    return null;
  }
}

async function main() {
  const useAI = process.argv.includes('--ai');
  const metadata = loadMetadata();

  let updated = 0;
  let noDesc = [];

  for (const dir of DIRS) {
    const dirPath = path.join(PROJECTS_ROOT, dir);
    if (!fs.existsSync(dirPath)) continue;

    const projects = fs.readdirSync(dirPath).filter(f => {
      const fullPath = path.join(dirPath, f);
      return fs.statSync(fullPath).isDirectory()
        && !f.startsWith('.')
        && !f.endsWith('.zip');
    });

    for (const proj of projects) {
      const projectPath = path.join(dirPath, proj);

      // 初始化项目元数据
      if (!metadata[proj]) {
        metadata[proj] = {};
      }

      // 只有没有描述或描述为空时才更新
      if (!metadata[proj].desc) {
        const desc = extractDescription(projectPath);
        if (desc) {
          metadata[proj].desc = desc;
          metadata[proj].descSource = 'auto';
          metadata[proj].descUpdated = new Date().toISOString().split('T')[0];
          updated++;
          console.log(`[更新] ${proj}: ${desc}`);
        } else {
          noDesc.push(`${dir}/${proj}`);
        }
      }

      // 记录位置
      metadata[proj].location = dir;
    }
  }

  saveMetadata(metadata);

  console.log(`\n✅ 更新了 ${updated} 个项目描述`);

  if (noDesc.length > 0) {
    console.log(`\n⚠️ ${noDesc.length} 个项目没有描述：`);
    noDesc.slice(0, 10).forEach(p => console.log(`   - ${p}`));
    if (noDesc.length > 10) {
      console.log(`   ... 还有 ${noDesc.length - 10} 个`);
    }
  }
}

main();
