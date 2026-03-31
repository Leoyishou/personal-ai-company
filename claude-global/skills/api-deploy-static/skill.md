---
name: deploy-static
description: "一键部署静态网站到 Vercel 和 Cloudflare Pages。支持 HTML/React/Vue 等任意静态项目。"
allowed-tools: Bash, Read, Write, Glob
---

# 静态网站部署 Skill

将当前目录的静态网站一键部署到 Vercel 和/或 Cloudflare Pages。

## 触发条件

用户提到以下意图时触发：

- "部署到 Vercel"
- "部署到 Cloudflare"
- "发布这个网站"
- "部署静态站点"
- "deploy to vercel/cloudflare"
- "/deploy"

## 前置条件

环境变量（已配置在 `~/.claude/secrets.env`）：

```bash
export VERCEL_TOKEN="xxx"
export CLOUDFLARE_API_TOKEN="xxx"
```

## 执行流程

### 1. 检查项目状态

```bash
# 确认在项目目录
pwd
ls -la

# 检查是否有 index.html 或构建产物
ls index.html 2>/dev/null || ls dist/index.html 2>/dev/null || ls build/index.html 2>/dev/null
```

### 2. 初始化 Git（如需要）

```bash
# 如果不是 git 仓库，初始化
git init

# 提交代码
git add .
git commit -m "Initial commit" || git commit -m "Update"
```

### 3. 创建 GitHub 仓库（如需要）

```bash
# 从目录名生成仓库名
REPO_NAME=$(basename $(pwd))

# 创建并推送
gh repo create $REPO_NAME --public --source=. --push
```

### 4. 部署到 Vercel

```bash
source ~/.claude/secrets.env

# 部署到生产环境
npx vercel --prod --token "$VERCEL_TOKEN" --yes
```

**输出示例**：
```
Aliased: https://project-name.vercel.app
```

### 5. 部署到 Cloudflare Pages

```bash
source ~/.claude/secrets.env

# 首次需要创建项目
npx wrangler pages project create $PROJECT_NAME --production-branch main 2>/dev/null || true

# 部署（指定目录，默认当前目录）
npx wrangler pages deploy . --project-name $PROJECT_NAME --commit-dirty=true
```

**输出示例**：
```
✨ Deployment complete! Take a peek over at https://xxx.project-name.pages.dev
```

## 部署目录说明

| 项目类型 | 部署目录 |
|----------|----------|
| 纯 HTML | `.`（当前目录） |
| Vite/React | `dist` |
| Next.js (静态导出) | `out` |
| Create React App | `build` |

如果有构建步骤，先运行构建：

```bash
npm run build
npx wrangler pages deploy dist --project-name $PROJECT_NAME
```

## 平台对比

| 特性 | Vercel | Cloudflare Pages |
|------|--------|------------------|
| 免费额度 | 100GB/月 | 无限带宽 |
| 构建速度 | 快 | 更快 |
| CDN 覆盖 | 全球 | 全球（更密集） |
| SSR 支持 | 原生 Next.js | Workers 适配 |
| 域名 | xxx.vercel.app | xxx.pages.dev |

## 常用参数

### Vercel

```bash
# 预览部署（非生产）
npx vercel --token "$VERCEL_TOKEN" --yes

# 生产部署
npx vercel --prod --token "$VERCEL_TOKEN" --yes

# 指定项目名
npx vercel --prod --token "$VERCEL_TOKEN" --yes --name my-project
```

### Cloudflare Pages

```bash
# 部署指定目录
npx wrangler pages deploy ./dist --project-name my-project

# 忽略 git 未提交警告
npx wrangler pages deploy . --project-name my-project --commit-dirty=true

# 列出所有项目
npx wrangler pages project list
```

## 自定义域名

### Vercel

```bash
# 添加域名
npx vercel domains add example.com --token "$VERCEL_TOKEN"
```

或在 https://vercel.com/dashboard 项目设置中添加。

### Cloudflare Pages

在 https://dash.cloudflare.com/ → Workers & Pages → 项目 → Custom domains 中添加。

## 完整示例

```bash
# 一键部署到两个平台
source ~/.claude/secrets.env
PROJECT_NAME=$(basename $(pwd))

# Git 提交
git add . && git commit -m "Update" || true

# 并行部署
npx vercel --prod --token "$VERCEL_TOKEN" --yes &
npx wrangler pages deploy . --project-name $PROJECT_NAME --commit-dirty=true &
wait

echo "Done!"
```
