import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            NativePlayerView()
                .tabItem { Label("Native", systemImage: "play.circle") }

            RNContainerView()
                .tabItem { Label("RN", systemImage: "bolt.horizontal.circle") }

            WebPlayerView()
                .tabItem { Label("H5", systemImage: "safari") }
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
            .environmentObject(AudioCenter.shared)
    }
}

