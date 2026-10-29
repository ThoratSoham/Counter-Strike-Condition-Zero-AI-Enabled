import os
import time
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf
import keyboard

class SpeechToTextListener:
    def __init__(self, key="v", sample_rate=16000, model_name="tiny.en", on_transcription=None):
        self.key = key.lower()
        self.sample_rate = sample_rate
        self.model_name = model_name
        self.on_transcription = on_transcription
        self.is_recording = False
        self.audio_frames = []
        self.whisper_model = None
        self._model_loading = False
        self.running = False
        self._lock = threading.Lock()

    def load_model(self):
        """Pre-load Whisper model in background."""
        if self.whisper_model is not None or self._model_loading:
            return
        self._model_loading = True
        def _load():
            try:
                import whisper
                print(f"[STT] Loading Whisper model '{self.model_name}' on CPU...")
                self.whisper_model = whisper.load_model(self.model_name, device="cpu")
                print("[STT] Whisper model loaded and ready.")
            except Exception as e:
                print(f"[STT] Failed to load Whisper: {e}")
            finally:
                self._model_loading = False

        t = threading.Thread(target=_load, daemon=True)
        t.start()

    def start_listening(self):
        """Start global push-to-talk key listener."""
        if self.running:
            return
        self.running = True
        self.load_model()
        
        try:
            keyboard.on_press_key(self.key, self._on_key_down)
            keyboard.on_release_key(self.key, self._on_key_up)
            print(f"[STT] Push-to-talk active! Hold '{self.key.upper()}' to speak to your teammates.")
        except Exception as e:
            print(f"[STT] Keyboard hook warning: {e}. (Ensure running with standard permissions)")

    def stop_listening(self):
        self.running = False
        try:
            keyboard.unhook_all()
        except Exception:
            pass

    def _audio_callback(self, indata, frames, time_info, status):
        if self.is_recording:
            self.audio_frames.append(indata.copy())

    def _on_key_down(self, event):
        with self._lock:
            if self.is_recording:
                return
            self.is_recording = True
            self.audio_frames = []
            print(f"[STT] 🎙️ Recording mic (push-to-talk active)...")
            
            try:
                self.stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype='float32',
                    callback=self._audio_callback
                )
                self.stream.start()
            except Exception as e:
                print(f"[STT] Failed to start mic stream: {e}")
                self.is_recording = False

    def _on_key_up(self, event):
        with self._lock:
            if not self.is_recording:
                return
            self.is_recording = False
            print(f"[STT] 🛑 Recording stopped, transcribing...")
            
            try:
                if hasattr(self, 'stream') and self.stream:
                    self.stream.stop()
                    self.stream.close()
            except Exception:
                pass

            if not self.audio_frames:
                return

            frames = self.audio_frames
            self.audio_frames = []

        # Process in separate worker thread to avoid blocking keyboard hook
        threading.Thread(target=self._process_audio, args=(frames,), daemon=True).start()

    def _process_audio(self, frames):
        try:
            audio_data = np.concatenate(frames, axis=0)
            duration = len(audio_data) / self.sample_rate
            if duration < 0.4:
                # Too short to be intentional speech
                return

            # Save to temporary wav
            temp_wav = "stt_temp.wav"
            sf.write(temp_wav, audio_data, self.sample_rate)

            # Transcribe
            if self.whisper_model is None:
                import whisper
                self.whisper_model = whisper.load_model(self.model_name, device="cpu")

            result = self.whisper_model.transcribe(temp_wav, fp16=False, language="en")
            transcription = result.get("text", "").strip()

            if os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except Exception:
                    pass

            if transcription:
                print(f"[STT] 🗣️ Player said: \"{transcription}\"")
                if self.on_transcription:
                    self.on_transcription(transcription)
        except Exception as e:
            print(f"[STT] Transcription error: {e}")

    def test_record(self, duration_sec=3):
        """Record for N seconds and return transcribed text (used by UI Check tool)."""
        print(f"[STT] Recording {duration_sec}s test audio from default mic...")
        audio = sd.rec(int(duration_sec * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype='float32')
        sd.wait()
        
        temp_wav = "stt_test.wav"
        sf.write(temp_wav, audio, self.sample_rate)
        
        if self.whisper_model is None:
            import whisper
            self.whisper_model = whisper.load_model(self.model_name, device="cpu")
            
        result = self.whisper_model.transcribe(temp_wav, fp16=False)
        text = result.get("text", "").strip()
        if os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except Exception:
                pass
        return text
