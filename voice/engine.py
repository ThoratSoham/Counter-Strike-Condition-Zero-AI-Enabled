import os
import json
import random
import asyncio
import io
import edge_tts
from voice.player import AudioPlayer

class VoiceEngine:
    def __init__(self, base_dir=None, language="en", volume=1.0, spatial=True):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_dir = base_dir
        self.language = language
        self.library_dir = os.path.join(self.base_dir, "voice", "library")
        self.lines_file = os.path.join(self.base_dir, "voice", "lines.json")
        self.personalities_dir = os.path.join(self.base_dir, "personalities")
        
        os.makedirs(self.library_dir, exist_ok=True)
        
        self.player = AudioPlayer()
        self.player.set_volume(volume)
        self.player.set_spatial(spatial)
        
        self.lines_db = self._load_json(self.lines_file, {})
        self.personalities = self._load_personalities()
        self.last_played = {}

    def _load_json(self, path, default):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[VoiceEngine] Error reading {path}: {e}")
        return default

    def _load_personalities(self):
        pers = {}
        if os.path.exists(self.personalities_dir):
            for fname in os.listdir(self.personalities_dir):
                if fname.endswith(".json"):
                    fpath = os.path.join(self.personalities_dir, fname)
                    data = self._load_json(fpath, None)
                    if data and "id" in data:
                        pers[data["id"]] = data
        return pers

    def get_personality(self, teammate_id):
        return self.personalities.get(teammate_id, {})

    def select_line(self, teammate_id: str, situation: str):
        """
        Select an emotional voice line for a teammate and situation, avoiding immediate repeats.
        """
        t_lines = self.lines_db.get(teammate_id, {})
        options = t_lines.get(situation, [])
        if not options:
            return None, None, 0

        # Avoid playing the exact same index twice in a row
        last_idx = self.last_played.get(f"{teammate_id}_{situation}", -1)
        if len(options) > 1:
            available = [i for i in range(len(options)) if i != last_idx]
            chosen_idx = random.choice(available)
        else:
            chosen_idx = 0

        self.last_played[f"{teammate_id}_{situation}"] = chosen_idx
        chosen_line = options[chosen_idx]
        return chosen_line.get("text"), chosen_line.get("emotion"), chosen_idx

    def get_library_path(self, teammate_id: str, situation: str, index: int) -> str:
        t_dir = os.path.join(self.library_dir, teammate_id)
        return os.path.join(t_dir, f"{situation}_{index}.mp3")

    def play_situation(self, teammate_id: str, situation: str, priority: int = 5):
        """
        Play a situation voice line: Layer 1 (pre-generated) or fallback to Layer 2 (live TTS).
        Returns (spoken_text, emotion)
        """
        text, emotion, index = self.select_line(teammate_id, situation)
        if not text:
            return None, None

        pers = self.get_personality(teammate_id)
        pan = pers.get("voice", {}).get("spatial_pan", 0.0)

        # Layer 1: Check pre-generated library
        lib_path = self.get_library_path(teammate_id, situation, index)
        if os.path.exists(lib_path):
            self.player.play_file(lib_path, pan=pan, priority=priority)
            return text, emotion

        # Layer 2: Live Edge-TTS synthesis on demand
        self.speak_live(teammate_id, text, emotion=emotion, priority=priority)
        return text, emotion

    def speak_live(self, teammate_id: str, text: str, emotion: str = None, priority: int = 5):
        """
        Synthesize custom text live with neural emotional settings and play asynchronously.
        """
        pers = self.get_personality(teammate_id)
        voice_cfg = pers.get("voice", {})
        pan = voice_cfg.get("spatial_pan", 0.0)
        
        # Choose voice by language
        if self.language == "hi" and "voice_hi" in voice_cfg:
            voice_name = voice_cfg.get("voice_hi", "en-IN-PrabhatNeural")
        else:
            voice_name = voice_cfg.get("voice_en", "en-US-GuyNeural")

        pitch = voice_cfg.get("pitch", "+0Hz")
        rate = voice_cfg.get("rate", "+0%")

        # Slight pitch/rate modulation based on emotion
        if emotion in ["screaming", "hyped", "panicked"]:
            pitch = "+4Hz"
            rate = "+12%"
        elif emotion in ["whispering", "calm"]:
            pitch = "-3Hz"
            rate = "-8%"
        elif emotion in ["angry", "tilted"]:
            pitch = "+2Hz"
            rate = "+8%"

        async def _synthesize():
            try:
                communicate = edge_tts.Communicate(text, voice_name, pitch=pitch, rate=rate)
                buf = io.BytesIO()
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        buf.write(chunk["data"])
                buf.seek(0)
                audio_bytes = buf.read()
                if audio_bytes:
                    self.player.play_data(audio_bytes, pan=pan, priority=priority)
            except Exception as e:
                print(f"[VoiceEngine] Live TTS failed for {teammate_id}: {e}")

        # Run async in background without blocking
        threading_loop = asyncio.new_event_loop()
        import threading
        t = threading.Thread(target=lambda: threading_loop.run_until_complete(_synthesize()), daemon=True)
        t.start()
