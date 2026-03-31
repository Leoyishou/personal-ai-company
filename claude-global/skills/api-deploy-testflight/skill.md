---
name: eas-testflight
description: 将 Expo/React Native 项目通过 EAS Build 构建 iOS 包并提交到 TestFlight。支持从零配置 EAS、构建、提交全流程。
---

# EAS TestFlight 部署 Skill

将任意 Expo/React Native 项目构建为 iOS 应用并提交到 TestFlight，用户可直接在 iPhone 上安装测试。

## When to Use

用户提到以下意图时触发：

- "帮我打包到 TestFlight"
- "构建 iOS 版本"
- "我要在 iPhone 上测试这个 app"
- "发布到 TestFlight"
- "eas build"
- "打 iOS 包"

## 前置要求

1. **Node.js + pnpm/npm** 已安装
2. **EAS CLI** 已安装（如没有会自动安装）
3. **Apple Developer 账号** 已配置（EAS 会引导登录）
4. 项目必须是 Expo 或 React Native (with Expo) 项目

## 完整工作流

### Phase 1: 项目检查与初始化

**Step 1.1: 检查项目类型**

```bash
# 检查是否有 expo 依赖
cat package.json | grep -q '"expo"' && echo "IS_EXPO=true" || echo "IS_EXPO=false"

# 检查是否已有 eas.json
ls eas.json 2>/dev/null && echo "HAS_EAS=true" || echo "HAS_EAS=false"

# 检查是否有 app.json 或 app.config.ts/js
ls app.json app.config.ts app.config.js 2>/dev/null
```

**Step 1.2: 如果不是 Expo 项目，需要先初始化**

```bash
# 安装 expo 依赖
npx install-expo-modules@latest

# 或者创建新 Expo 项目（如果是从零开始）
npx create-expo-app@latest my-app
```

**Step 1.3: 确保 EAS CLI 已安装**

```bash
# 检查 eas-cli
npx eas-cli --version 2>/dev/null || npm install -g eas-cli

# 登录 EAS（如果未登录）
npx eas-cli whoami || npx eas-cli login
```

### Phase 2: 配置 EAS

**Step 2.1: 初始化 EAS 项目（如果没有 eas.json）**

```bash
npx eas-cli init
```

这会：
- 创建 EAS 项目并获取 projectId
- 在 app.config 中写入 `extra.eas.projectId`

**Step 2.2: 创建/更新 eas.json**

确保 eas.json 包含 production profile：

```json
{
  "cli": {
    "version": ">= 3.0.0",
    "appVersionSource": "remote"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal"
    },
    "production": {
      "autoIncrement": true
    }
  },
  "submit": {
    "production": {
      "ios": {
        "appleId": "用户的 Apple ID",
        "ascAppId": "App Store Connect App ID（首次会自动创建）",
        "appleTeamId": "Apple Team ID"
      }
    }
  }
}
```

**Step 2.3: 配置 iOS 相关设置**

确保 app.config.ts/app.json 中包含：

```typescript
{
  ios: {
    supportsTablet: true,
    bundleIdentifier: "com.yourname.appname", // 唯一 bundle ID
    infoPlist: {
      ITSAppUsesNonExemptEncryption: false  // 避免 TestFlight 审核卡住
    }
  }
}
```

重要配置项：
- `bundleIdentifier`: iOS 唯一标识符，格式 `com.company.appname`
- `ITSAppUsesNonExemptEncryption: false`: 声明不使用非豁免加密，跳过出口合规审核

### Phase 3: 构建 iOS 包

**Step 3.1: 运行 EAS Build**

```bash
npx eas-cli build --platform ios --profile production --non-interactive
```

参数说明：
- `--platform ios`: 只构建 iOS
- `--profile production`: 使用 production 配置（用于 App Store / TestFlight）
- `--non-interactive`: 非交互模式（首次可能需要去掉此参数以完成 Apple 登录）

**首次构建注意事项：**
- EAS 会提示输入 Apple Developer 账号凭据
- 会自动创建 provisioning profile 和 certificates
- 如果没有 App Store Connect 中的 app，会提示创建

**Step 3.2: 等待构建完成**

构建是远程进行的，通常需要等待。可以通过以下方式查看状态：

```bash
# 查看构建状态
npx eas-cli build:list --platform ios --limit 1

# 或通过 URL 查看（构建开始时会输出 URL）
```

### Phase 4: 提交到 TestFlight

**Step 4.1: 使用 EAS Submit**

构建完成后，提交到 TestFlight：

```bash
npx eas-cli submit --platform ios --profile production --latest --non-interactive
```

参数说明：
- `--latest`: 使用最新的构建产物
- 也可以用 `--id BUILD_ID` 指定具体构建

**Step 4.2: 首次提交配置**

首次提交需要提供：
- Apple ID（邮箱）
- App-specific password（在 appleid.apple.com 生成）或 ASC API Key
- Apple Team ID

推荐使用 ASC API Key（更稳定）：
```bash
# 使用 App Store Connect API Key
npx eas-cli submit --platform ios \
  --asc-api-key-path /path/to/AuthKey_XXXXX.p8 \
  --asc-api-key-id XXXXX \
  --asc-api-key-issuer-id XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
```

### Phase 5: 验证与通知

**Step 5.1: 确认提交状态**

```bash
npx eas-cli submit:list --platform ios --limit 1
```

**Step 5.2: TestFlight 处理**

提交成功后：
1. Apple 会自动处理（通常几分钟到半小时）
2. 处理完成后，TestFlight 中的测试人员会收到通知
3. 如果是首次提交新 app，需要在 App Store Connect 中：
   - 填写基本信息
   - 添加内部/外部测试人员
   - 接受合规声明

## 一键命令（构建+提交）

如果一切已配置好，可以直接：

```bash
npx eas-cli build --platform ios --profile production --non-interactive --auto-submit
```

`--auto-submit` 会在构建完成后自动提交到 TestFlight。

## 常见问题

### Q: 构建失败提示 provisioning profile 问题？
A: 运行 `npx eas-cli credentials` 重新配置 iOS 凭据。

### Q: 提交失败提示 App Store Connect 权限？
A: 确保 Apple ID 有 App Store Connect 的 Admin 或 App Manager 权限。

### Q: TestFlight 里看不到新版本？
A:
1. 检查 App Store Connect 中 TestFlight 标签页
2. 可能正在"处理中"状态
3. 如果显示"缺少合规信息"，需要在 ASC 中点击"管理"并回答加密问题
4. 设置 `ITSAppUsesNonExemptEncryption: false` 可自动跳过此步骤

### Q: 如何添加测试人员？
A: 在 App Store Connect → TestFlight → 内部测试 → 添加测试人员邮箱

### Q: 构建很慢怎么办？
A: 免费账号有排队，付费 EAS 订阅可获得优先构建队列。

## 快速参考

| 命令 | 用途 |
|------|------|
| `npx eas-cli login` | 登录 EAS |
| `npx eas-cli init` | 初始化 EAS 项目 |
| `npx eas-cli build -p ios` | 构建 iOS |
| `npx eas-cli submit -p ios --latest` | 提交最新构建到 TestFlight |
| `npx eas-cli build -p ios --auto-submit` | 构建并自动提交 |
| `npx eas-cli build:list` | 查看构建历史 |
| `npx eas-cli credentials` | 管理凭据 |
| `npx eas-cli whoami` | 查看当前登录用户 |

## 参考项目

已有成功案例：`/Users/liuyishou/usr/projects/inbox/my-first-iphone-app/`
- EAS Project ID: `07400361-d7fc-462b-a24b-86e0aa3dd704`
- Bundle ID: `space.manus.my.first.iphone.app.t20260121010932`
- 使用 Expo SDK 54 + React Native 0.81.5
