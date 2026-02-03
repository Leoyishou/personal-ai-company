import Foundation
import AVFoundation
import Combine

@objcMembers
final class AudioCenter: NSObject, ObservableObject {
    static let shared = AudioCenter()

    @Published private(set) var isPlaying: Bool = false

    private var player: AVPlayer?
    private let streamURL = URL(string: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")!

    private override init() {
        super.init()
        configureSession()
        preparePlayer()
    }

    func toggle() {
        isPlaying ? pause() : play()
    }

    func play() {
        if player == nil { preparePlayer() }
        player?.play()
        isPlaying = true
    }

    func pause() {
        player?.pause()
        isPlaying = false
    }

    func isPlayingValue() -> Bool { isPlaying }

    private func preparePlayer() {
        let item = AVPlayerItem(url: streamURL)
        player = AVPlayer(playerItem: item)
    }

    private func configureSession() {
        let session = AVAudioSession.sharedInstance()
        try? session.setCategory(.playback, mode: .default)
        try? session.setActive(true)
    }
}

