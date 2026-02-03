import SwiftUI

struct NativePlayerView: View {
    @EnvironmentObject var audio: AudioCenter

    var body: some View {
        VStack(spacing: 20) {
            Text("Native Player")
                .font(.largeTitle).bold()
            Button(action: { audio.toggle() }) {
                Text(audio.isPlaying ? "Pause" : "Play")
                    .font(.title2)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 10)
                    .background(Color.accentColor.opacity(0.15))
                    .cornerRadius(12)
            }
            Text("Status: \(audio.isPlaying ? "Playing" : "Paused")")
                .foregroundColor(.secondary)
        }
        .padding()
    }
}

struct NativePlayerView_Previews: PreviewProvider {
    static var previews: some View {
        NativePlayerView().environmentObject(AudioCenter.shared)
    }
}

