import SwiftUI
import WebKit

final class WebPlayerCoordinator: NSObject, WKScriptMessageHandler {
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.name == "audio" else { return }
        if let action = message.body as? String, action == "toggle" {
            AudioCenter.shared.toggle()
        }
    }
}

struct WebPlayerView: UIViewRepresentable {
    func makeCoordinator() -> WebPlayerCoordinator { WebPlayerCoordinator() }

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.userContentController.add(context.coordinator, name: "audio")
        let webView = WKWebView(frame: .zero, configuration: config)

        if let url = Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: "Web") {
            webView.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
        } else {
            let html = """
            <html><body style='font-family:-apple-system'>
            <p>Web/index.html not found in bundle.</p>
            </body></html>
            """
            webView.loadHTMLString(html, baseURL: nil)
        }
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) { }
}

