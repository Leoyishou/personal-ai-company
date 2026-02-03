帮我用native、rn 和 h5 实现一个极简的 ios app，可以播放一段音频
做了什么

  - 新增统一实现目录：ios-hybrid/
      - Swift 源码
          - ios-hybrid/Sources/DejavuHybridApp.swift:1
          - ios-hybrid/Sources/ContentView.swift:1
          - ios-hybrid/Sources/AudioCenter.swift:1（共享 AVPlayer，Native/RN/H5 可共用）
          - ios-hybrid/Sources/NativePlayerView.swift:1
          - ios-hybrid/Sources/RNContainerView.swift:1（加载 RN RCTRootView）
          - ios-hybrid/Sources/WebPlayerView.swift:1（加载 WKWebView）
      - RN 代码
          - ios-hybrid/ReactNative/package.json:1
          - ios-hybrid/ReactNative/index.js:1（注册组件名 DejavuRN）
          - ios-hybrid/ReactNative/App.jsx:1（按钮调用原生模块播放/暂停）
      - H5 页面
          - ios-hybrid/Web/index.html:1（既能用 <audio> 播放，也能调用原生播放）
      - RN 原生模块（桥接）
          - ios-hybrid/Bridge/AudioControllerModule.m:1（JS 调用 AudioCenter.shared 的 play/pause/toggle）
      - CocoaPods
          - ios-hybrid/ios/Podfile:1（集成 React Native 运行时）
      - 说明
          - ios-hybrid/README.md:1（完整搭建与真机安装步骤）

  音频源默认使用同一个 HTTPS MP3，避免 ATS 问题：

  - https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3

  如何打到 iPhone（一步步）

  - 前置
      - Mac 安装 Xcode、CocoaPods；iPhone 连接电脑；Apple ID 登录 Xcode。
      - 安装 Node 18+（用于打包 RN JS）。
      1. 用 Xcode 建工程
      - 新建 iOS App（SwiftUI/Swift），命名为 DejavuHybrid。
      - 将 ios-hybrid/Sources/*.swift、ios-hybrid/Bridge/AudioControllerModule.m、ios-hybrid/Web/index.html 拖入工程（勾选 Add to targets）。
      2. 集成 React Native（Pods）
      - 安装依赖：cd ios-hybrid/ReactNative && npm install
      - 安装 Pods：cd ../ios && pod install
      - 之后用 DejavuHybrid.xcworkspace 打开工程。
      3. 打包 RN JS（离线 bundle）
      - cd ios-hybrid/ReactNative
      - 运行：
          - npx react-native bundle --platform ios --dev false --entry-file index.js --bundle-output ../ios/main.jsbundle --assets-dest ../ios
      - 将生成的 ios-hybrid/ios/main.jsbundle 拖入 Xcode 工程并加入 DejavuHybrid target 的 Copy Bundle Resources。
      - 可选：Xcode Build Phases 添加 Run Script，内容：
          - export NODE_BINARY=node
          - ../ReactNative/node_modules/react-native/scripts/react-native-xcode.sh
      4. 签名与运行
      - Target > Signing & Capabilities 勾选 “Automatically manage signing”，选择你的 Team。
      - 选择你的 iPhone 作为运行设备，点击 Run ▶ 真机安装。
      5. 使用说明
      - App 启动后为 Tab 界面：
          - Native：原生 SwiftUI 按钮控制 AudioCenter 播放/暂停。
          - RN：RN 页面按钮通过 AudioController 原生模块控制同一播放器。
          - H5：网页内可用 <audio> 自行播放，或点击“Native: Toggle”按钮让网页调用原生播放器。

  注意与可定制

  - 若 Target 名称不是 DejavuHybrid：
      - 请把 ios-hybrid/Bridge/AudioControllerModule.m:4 里的 #import "DejavuHybrid-Swift.h" 改成 <你的模块名>-Swift.h。
  - RN 离线包路径：
      - RNContainerView 会从主 Bundle 读取 main.jsbundle，未找到时会显示提示文本。
  - 更换音频：
      - 在 ios-hybrid/Sources/AudioCenter.swift:1 修改 streamURL 为你的 HTTPS 链接；或改为 Bundle 内本地文件。
  - 若想让 H5 全程走原生播放：
      - 可删掉 <audio>，只保留调用 window.webkit.messageHandlers.audio.postMessage('toggle') 的按钮。

  需要我把完整的 Xcode 项目文件也直接生成到仓库里（含 .xcodeproj/.xcworkspace），或者帮你把 Bundle/Pods/签名都联调一遍？我可以继续完善。