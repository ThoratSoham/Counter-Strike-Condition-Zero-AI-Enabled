import threading
import queue
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
import os
import io

class AudioPlayer:
    """
    Audio player manager.
    Note: Per Step 4, meme sounds are played directly inside the Condition Zero engine
    via AMX Mod X `client_cmd(0, "spk ...")` from `czero/sound/ai_teammates/<tag>/*.wav`.
    External OS playback is disabled by default so sounds NEVER play outside the game.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AudioPlayer, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, sample_rate=22050, external_enabled=False):
        if getattr(self, "_initialized", False):
            return
        self.sample_rate = sample_rate
        self.external_enabled = external_enabled
        self.queue = queue.PriorityQueue()
        self.is_playing = False
        self.volume = 1.0
        self.spatial_enabled = True
        self.stop_requested = False

        self.worker_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.worker_thread.start()
        self._initialized = True

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(2.0, volume))

    def set_spatial(self, enabled: bool):
        self.spatial_enabled = enabled

    def play_file(self, file_path: str, pan: float = 0.0, priority: int = 5):
        """
        Queue an audio file for playback if external playback is explicitly enabled.
        """
        if not os.path.exists(file_path):
            return False
        if not self.external_enabled:
            # In-engine GoldSrc playback handles audio via `spk`; do not play outside the game.
            return True
        self.queue.put((priority, time.time(), file_path, pan))
        return True

    def play_data(self, audio_bytes: bytes, pan: float = 0.0, priority: int = 5):
        if not self.external_enabled:
            return True
        self.queue.put((priority, time.time(), audio_bytes, pan))
        return True

    def clear_queue(self):
        """Clear pending audio lines."""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except queue.Empty:
                break

    def stop_all(self):
        """Immediately purge queue and halt any active audio playback."""
        self.clear_queue()
        self.is_playing = False
        try:
            sd.stop()
        except Exception:
            pass

    def _apply_panning(self, data: np.ndarray, pan: float) -> np.ndarray:
        if data.ndim == 1:
            left = data * np.cos((pan + 1.0) * np.pi / 4.0)
            right = data * np.sin((pan + 1.0) * np.pi / 4.0)
            return np.column_stack((left, right))
        elif data.ndim == 2:
            if data.shape[1] == 1:
                mono = data[:, 0]
                left = mono * np.cos((pan + 1.0) * np.pi / 4.0)
                right = mono * np.sin((pan + 1.0) * np.pi / 4.0)
                return np.column_stack((left, right))
            else:
                left_gain = max(0.0, min(1.0, 1.0 - pan * 0.5))
                right_gain = max(0.0, min(1.0, 1.0 + pan * 0.5))
                stereo = data.copy()
                stereo[:, 0] *= left_gain
                stereo[:, 1] *= right_gain
                return stereo
        return data

    def _playback_loop(self):
        while not self.stop_requested:
            try:
                item = self.queue.get(timeout=0.2)
            except queue.Empty:
                continue

            priority, timestamp, audio_source, pan = item
            if not self.external_enabled:
                self.queue.task_done()
                continue

            self.is_playing = True
            try:
                if isinstance(audio_source, str):
                    data, fs = sf.read(audio_source, dtype='float32')
                elif isinstance(audio_source, bytes):
                    buf = io.BytesIO(audio_source)
                    data, fs = sf.read(buf, dtype='float32')
                else:
                    self.queue.task_done()
                    continue

                data = data * self.volume
                if self.spatial_enabled:
                    data = self._apply_panning(data, pan)

                sd.play(data, samplerate=fs)
                sd.wait()
            except Exception as e:
                print(f"[AudioPlayer] Playback error: {e}")
            finally:
                self.is_playing = False
                self.queue.task_done()
