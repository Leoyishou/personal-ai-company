import SwiftUI
import React

struct RNContainerView: UIViewRepresentable {
    func makeUIView(context: Context) -> UIView {
        let view = UIView()
        view.backgroundColor = .systemBackground

        // Look for an offline bundle in the main bundle
        let jsBundleURL = Bundle.main.url(forResource: "main", withExtension: "jsbundle")

        guard let jsURL = jsBundleURL else {
            // Fallback placeholder when JS not bundled
            let label = UILabel()
            label.text = "RN bundle not found. Bundle JS as main.jsbundle."
            label.numberOfLines = 0
            label.textAlignment = .center
            label.textColor = .secondaryLabel
            label.translatesAutoresizingMaskIntoConstraints = false
            view.addSubview(label)
            NSLayoutConstraint.activate([
                label.centerXAnchor.constraint(equalTo: view.centerXAnchor),
                label.centerYAnchor.constraint(equalTo: view.centerYAnchor),
                label.leadingAnchor.constraint(greaterThanOrEqualTo: view.leadingAnchor, constant: 16),
                label.trailingAnchor.constraint(lessThanOrEqualTo: view.trailingAnchor, constant: -16)
            ])
            return view
        }

        let bridge = RCTBridge(bundleURL: jsURL, moduleProvider: nil, launchOptions: nil)
        let rootView = RCTRootView(bridge: bridge!, moduleName: "DejavuRN", initialProperties: nil)
        rootView.backgroundColor = UIColor.systemBackground
        rootView.translatesAutoresizingMaskIntoConstraints = false

        view.addSubview(rootView)
        NSLayoutConstraint.activate([
            rootView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            rootView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            rootView.topAnchor.constraint(equalTo: view.topAnchor),
            rootView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])

        return view
    }

    func updateUIView(_ uiView: UIView, context: Context) {}
}

