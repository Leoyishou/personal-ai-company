---
name: deploy
shortname: deploy
description: 统一部署入口 - 自动识别项目类型，支持 Web (Vercel/Cloudflare) 和 iOS (TestFlight)。
version: 1.0.0
author: Claude
allowed-tools: Bash, Read, Write, Glob
model: sonnet
tags: [deploy, vercel, cloudflare, testflight, ios, web]
---

# Deploy - 统一部署入口

## 架构概览

本 skill 采用**策略模式**，自动识别项目类型并选择部署目标：

```
┌─────────────────────────────────────────────────────────────┐
│                      deploy skill                            │
├─────────────────────────────────────────────────────────────┤
│  ProjectStrategy（项目类型）  │  TargetStrategy（部署目标）   │
│  - static (纯 HTML)          │  - vercel                     │
│  - vite/react/vue            │  - cloudflare                 │
│  - expo/react-native         │  - testflight                 │
│  - next.js                   │  - all (多平台)               │
└─────────────────────────────────────────────────────────────┘
```

---

## 一、策略调度规则

### 1.1 项目类型自动识别

| 特征文件 | 项目类型 | 默认目标 |
|---------|---------|---------|
| `app.json` + `expo` in package.json | Expo/RN | TestFlight |
| `next.config.*` | Next.js | Vercel |
| `vite.config.*` | Vite | Vercel + Cloudflare |
| `index.html` (根目录) | 纯静态 | Vercel + Cloudflare |
| `package.json` + react/vue | SPA | Vercel + Cloudflare |

### 1.2 用户意图识别

| 用户输入 | 目标 |
|---------|------|
| "部署" / "deploy" | 自动识别项目类型 |
| "部署到 Vercel" | vercel |
| "部署到 Cloudflare" | cloudflare |
| "打 iOS 包" / "TestFlight" | testflight |
| "部署到所有平台" | all |

---

## 二、Web 部署（Target: vercel / cloudflare）

### 2.1 前置检查

```bash
# 检查项目类型
ls package.json index.html vite.config.* next.config.* 2>/dev/null

# 检查构建产物目录
ls -d dist build out .next 2>/dev/null
```

### 2.2 构建（如需要）

```bash
# 检测并运行构建
if [ -f "package.json" ]; then
  npm run build 2>/dev/null || pnpm build 2>/dev/null
fi
```

### 2.3 部署到 Vercel

```bash
source ~/.claude/secrets.env

# 生产部署
npx vercel --prod --token "$VERCEL_TOKEN" --yes
```

### 2.4 部署到 Cloudflare Pages

```bash
source ~/.claude/secrets.env
PROJECT_NAME=$(basename $(pwd))

# 确定部署目录
DEPLOY_DIR="."
[ -d "dist" ] && DEPLOY_DIR="dist"
[ -d "build" ] && DEPLOY_DIR="build"
[ -d "out" ] && DEPLOY_DIR="out"

# 创建项目（首次）
npx wrangler pages project create $PROJECT_NAME --production-branch main 2>/dev/null || true

# 部署
npx wrangler pages deploy $DEPLOY_DIR --project-name $PROJECT_NAME --commit-dirty=true
```

### 2.5 并行部署

```bash
source ~/.claude/secrets.env
PROJECT_NAME=$(basename $(pwd))

# 并行部署到两个平台
npx vercel --prod --token "$VERCEL_TOKEN" --yes &
npx wrangler pages deploy . --project-name $PROJECT_NAME --commit-dirty=true &
wait

echo "部署完成！"
```

---

## 三、iOS 部署（Target: testflight）

### 3.1 前置检查

```bash
# 检查是否是 Expo 项目
cat package.json | grep -q '"expo"' && echo "IS_EXPO=true" || echo "IS_EXPO=false"

# 检查 EAS 配置
ls eas.json app.json app.config.* 2>/dev/null

# 检查 EAS CLI
npx eas-cli --version 2>/dev/null || npm install -g eas-cli
```

### 3.2 EAS 初始化（如需要）

```bash
# 登录 EAS
npx eas-cli whoami || npx eas-cli login

# 初始化项目
npx eas-cli init
```

### 3.3 构建并提交

```bash
# 构建 + 自动提交到 TestFlight
npx eas-cli build --platform ios --profile production --non-interactive --auto-submit
```

### 3.4 单独操作

```bash
# 仅构建
npx eas-cli build --platform ios --profile production --non-interactive

# 仅提交（使用最新构建）
npx eas-cli submit --platform ios --profile production --latest --non-interactive

# 查看构建状态
npx eas-cli build:list --platform ios --limit 1
```

---

## 四、凭证配置

### 4.1 环境变量（~/.claude/secrets.env）

```bash
# Vercel
VERCEL_TOKEN=xxx

# Cloudflare
CLOUDFLARE_API_TOKEN=xxx
```

### 4.2 EAS/Apple 凭证

| 信息 | 值 |
|-----|-----|
| Apple ID | 876538875@qq.com |
| Apple Team ID | 52LKR8ZM8L |
| EAS 用户 | luisleonard |

---

## 五、平台对比

| 特性 | Vercel | Cloudflare | TestFlight |
|------|:------:|:----------:|:----------:|
| Web 静态 | ✅ | ✅ | - |
| SSR/Next.js | ✅ | ⚠️ | - |
| iOS App | - | - | ✅ |
| 免费额度 | 100GB/月 | 无限带宽 | - |
| CDN | 全球 | 全球（更密集） | - |

---

## 六、输出格式

```
部署结果：
✅ Vercel: https://project-name.vercel.app
✅ Cloudflare: https://project-name.pages.dev
✅ TestFlight: 已提交，等待 Apple 处理

下一步：
- 测试人员将收到 TestFlight 通知
- 如需添加测试人员，访问 App Store Connect
```

---

## 七、故障排查

| 问题 | 解决方案 |
|------|---------|
| Vercel 认证失败 | 检查 VERCEL_TOKEN |
| Cloudflare 权限不足 | 检查 CLOUDFLARE_API_TOKEN 权限 |
| EAS 构建失败 | 运行 `npx eas-cli credentials` 重新配置 |
| TestFlight 处理中 | 等待 Apple 处理（几分钟到半小时） |
| 缺少合规信息 | 在 app.config 中设置 `ITSAppUsesNonExemptEncryption: false` |

---

## 八、底层 API

本 skill 封装了以下 API 层能力：

| API | 用途 |
|-----|------|
| `api-deploy-static` | Web 静态网站部署 (Vercel/Cloudflare) |
| `api-deploy-testflight` | iOS App 构建和 TestFlight 提交 |
