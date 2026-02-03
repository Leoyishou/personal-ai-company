Dejavu Hybrid (Native + RN + H5 in one iOS app)

目标
- 一个 iOS App，内含三种技术：
  - 原生 SwiftUI 视图（使用 AVFoundation 播放音频）
  - React Native 视图（JS 调用原生模块控制同一个播放器）
  - H5 视图（WKWebView 内嵌网页，网页按钮可调用原生播放/暂停）

结构
- Swift 源码: `ios-hybrid/Sources`（App 入口、Tab 容器、原生播放器、RN 容器、Web 容器、共享播放器）
- RN 代码: `ios-hybrid/ReactNative`（`index.js`、`App.jsx`）
- H5 页面: `ios-hybrid/Web/index.html`
- RN 原生模块（ObjC）: `ios-hybrid/Bridge/AudioControllerModule.m`
- CocoaPods: `ios-hybrid/ios/Podfile`

最终效果
- 一个包含 3 个 Tab 的 App：Native / RN / H5，三者共享同一个音频源与播放状态（Native 与 RN 通过同一个原生播放器；H5 在 WebView 内用 <audio> 播放，或可调用原生播放器）。

一、创建 Xcode 项目（SwiftUI）
1) 打开 Xcode > File > New > Project…
   - iOS App；Product Name: `DejavuHybrid`
   - Interface: SwiftUI; Language: Swift
   - 关闭 Core Data/Tests
2) 将以下文件添加进项目（拖入 Xcode 工程里，勾选 “Copy items if needed” 且 Add to targets 选择 `DejavuHybrid`）：
   - `ios-hybrid/Sources/DejavuHybridApp.swift`
   - `ios-hybrid/Sources/ContentView.swift`
   - `ios-hybrid/Sources/AudioCenter.swift`
   - `ios-hybrid/Sources/NativePlayerView.swift`
   - `ios-hybrid/Sources/RNContainerView.swift`
   - `ios-hybrid/Sources/WebPlayerView.swift`
   - `ios-hybrid/Bridge/AudioControllerModule.m`
   - `ios-hybrid/Web/index.html`（确保被加入 `Copy Bundle Resources`）

二、集成 React Native（CocoaPods）
1) 在本目录准备 RN 代码：
   - `cd ios-hybrid/ReactNative`
   - 安装 Node 依赖：`npm install`（如无 Node，请先安装 Node 18+）
2) 在 iOS 目录安装 Pods：
   - `cd ../ios`
   - 打开并检查 `Podfile` 中 target 名称是否为 `DejavuHybrid`（与 Xcode Target 同名）。
   - 运行 `pod install`
   - 用 CocoaPods 生成的 `DejavuHybrid.xcworkspace` 打开工程（之后都用 .xcworkspace）。

三、打包 RN JS Bundle
默认使用离线 bundle（无需运行 Metro）。在 `ios-hybrid/ReactNative` 执行：

```
npx react-native bundle \
  --platform ios \
  --dev false \
  --entry-file index.js \
  --bundle-output ../ios/main.jsbundle \
  --assets-dest ../ios
```

然后在 Xcode 中将生成的 `main.jsbundle`（以及可能的 image 资源）拖入工程并加入到 target 的 `Copy Bundle Resources`。

可选（自动化）：也可在 Xcode Target > Build Phases 添加一个 `Bundle React Native code and images` 的 Run Script，内容：

```
export NODE_BINARY=node
../ReactNative/node_modules/react-native/scripts/react-native-xcode.sh
```

四、H5 集成
- 已提供 `ios-hybrid/Web/index.html`，被 `WebPlayerView` 通过 `WKWebView` 加载。
- 网页内有两个按钮：
  - 直接用 `<audio>` 标签播放/暂停（纯 H5）
  - 调用 `window.webkit.messageHandlers.audio.postMessage('toggle')` 与原生交互，控制原生播放器。

五、代码签名与真机安装
1) Xcode 选择工程（蓝色图标）> Targets `DejavuHybrid` > Signing & Capabilities：
   - 勾选 “Automatically manage signing”
   - 选择你的 Apple ID/Team（免费开发者账号也可）
2) 插上 iPhone（或 Wi‑Fi 调试），选择你的 iPhone 作为运行设备，点击 Run ▶

六、常见问题
- RN 头文件导入：`AudioControllerModule.m` 引入的是 `DejavuHybrid-Swift.h`，若你的 Product Module Name 不是 `DejavuHybrid`，请相应改成 `<你的模块名>-Swift.h`。
- JS Bundle 路径：`RNContainerView` 默认尝试从主 Bundle 读取 `main.jsbundle`；若为空，将显示占位视图。
- ATS：音频为 HTTPS URL，默认无需额外配置。
- 若想让 H5 使用原生播放器而不是 `<audio>`，可在网页中仅调用 `postMessage('toggle')`，并移除 `<audio>`，完全走原生通路。

