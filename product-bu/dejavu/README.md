# Dejavu – Hybrid iOS App (Native + RN + H5)

Single iOS app combining three layers:
- Native SwiftUI view using AVFoundation
- React Native view bridged into the app
- H5 view embedded via WKWebView

All share the same audio controller (`AudioCenter`) or can use pure `<audio>` inside the WebView.

Start here
- Full setup and install guide: `ios-hybrid/README.md:1`

Key files
- Swift sources: `ios-hybrid/Sources/*.swift`
- RN bundle entry: `ios-hybrid/ReactNative/index.js:1`, `ios-hybrid/ReactNative/App.jsx:1`
- Web page: `ios-hybrid/Web/index.html:1`
- RN bridge module (ObjC): `ios-hybrid/Bridge/AudioControllerModule.m:1`
- Pods config: `ios-hybrid/ios/Podfile:1`

Audio source
- Default: `https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3` (HTTPS avoids ATS issues)

Notes
- If your Xcode target name differs from `DejavuHybrid`, update the import in `ios-hybrid/Bridge/AudioControllerModule.m:1` to `"<YourModule>-Swift.h"`.
