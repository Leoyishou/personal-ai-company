import SwiftUI

@main
struct DejavuHybridApp: App {
    @StateObject private var audio = AudioCenter.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(audio)
        }
    }
}

