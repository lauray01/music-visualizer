import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
from demo import ensure_ffmpeg
from pathlib import Path


def analyze(audio_path: Path, log_cb=print):
    # Ensure FFmpeg is reachable for compressed formats (safe to call always)
    ensure_ffmpeg(log_cb)

    audio_path = audio_path.expanduser().resolve(strict=True)
    out_dir = audio_path.parent
    out_prefix = audio_path.stem

    def out(name: str) -> Path:
        return out_dir / f"{out_prefix}_{name}.png"

    log_cb(f"[i] Audio: {audio_path}")
    log_cb(f"[i] Output dir: {out_dir}")

    # getting information about the audio file
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)

    stft = np.abs(librosa.stft(y, hop_length=512, n_fft=2048*4)) # * 4 for better resolution
    
    spectrogram = librosa.amplitude_to_db(stft, ref=np.max)
    
    librosa.display.specshow(spectrogram, sr=sr, hop_length=512, x_axis='time', y_axis='log')
    plt.title('Spectrogram')
    plt.colorbar(format='%+2.0f dB')
    plt.tight_layout()
    plt.show()
    
    #frequencies
    frequencies = librosa.core.fft_frequencies(sr=sr, n_fft=2048*4)
    
    #an array of time values corresponding to each frame in the STFT
    times = librosa.core.frames_to_time(np.arange(spectrogram.shape[1]), sr=sr, hop_length=512, n_fft=2048*4)
    time_index_ratio = len(times) / times[len(times)-1]  # ratio of time index to actual time in seconds we can do this because the sample rate is constant
    frequencies_index_ratio = len(frequencies)/frequencies[len(frequencies)-1]
    
    #since the spectrogram is a 2D array where the first dimension corresponds to frequency and the second dimension corresponds to time, we can define a function to get the decibel value at a specific time and frequency
    def get_decibel(target_time, frequency):
        return spectrogram[int(frequency * frequencies_index_ratio), int(target_time * time_index_ratio)]
    
    
    
