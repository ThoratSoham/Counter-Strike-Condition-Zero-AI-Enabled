import os
import re
import json
import time
import wave
import random
from collections import defaultdict
import numpy as np
import soundfile as sf
from voice.player import AudioPlayer

KNOWN_TAGS = [
    "hype",
    "kill_headshot",
    "shock",
    "praise",
    "roast",
    "hindi_swear",
    "fail_sad",
    "apology_getup",
    "shut_up",
    "greeting",
    "laugh",
    "goodbye"
]

FRIENDLY_NAMES = {
    "01_hell_yeaaaaah.mp3": "hell yeah",
    "02_oh_yeah_meme.mp3": "oh yeah",
    "03_oh_yessss.mp3": "oh yes",
    "04_yessss_nathan_online_audio_converter.mp3": "yes!",
    "05_yeahh_boiiiiiiii.mp3": "yeah boy",
    "06_yeah_buddy_lightweight.mp3": "yeah buddy",
    "07_sheeshsoundeffect1.mp3": "sheesh",
    "08_maja_aaya.mp3": "maja aaya",
    "09_mickey_mouse_oh_boy.mp3": "oh boy",
    "01_boomheadshot_swf.mp3": "boom headshot",
    "02_1_booom_1.mp3": "boom",
    "03_wtf_boom_sound_meme.mp3": "wtf boom",
    "01_oh_my_god_meme.mp3": "oh my god",
    "02_oh_my_god_bro_ah_hell_nah.mp3": "hell nah",
    "03_modis_oh_my_god.mp3": "oh my god",
    "04_kevin_heart_damn.mp3": "damn",
    "05_dammmm_daniel.mp3": "damn daniel",
    "01_modi_ji_wah.mp3": "wah",
    "02_gian_hain_aap.mp3": "gian hain aap",
    "03_sochna_pdta_hai_re_hindustani_bhau.mp3": "sochna padta hai",
    "01_bruh_sound_effect_wstdzdm.mp3": "bruh",
    "02_ye_kya_bak_rahe_ho_mc.mp3": "ye kya bak rahe ho",
    "03_is_sajjan_ko_kya_takleef_hai_bhai.mp3": "kya takleef hai bhai",
    "04_tejaswi_modi_can_be_used_as_a_taunt_to_t.mp3": "tejaswi log",
    "05_masti_dekho_bc_cid_dubbing.mp3": "masti dekho",
    "06_is_ka_karan_narendar_modi.mp3": "iska karan",
    "01_kyu_re_madarchod_cid.mp3": "kyu re",
    "02_lavden_bhojyam.mp3": "lavden bhojyam",
    "03_modi_ji_bkl.mp3": "bkl",
    "04_there_a_guy_fucking_me_in_the_ass.mp3": "rage scream",
    "01_spongebob_disappointed_sound_effect_isep.mp3": "sad trombone",
    "02_banana_cat_crying.mp3": "banana cat crying",
    "03_depression_indian.mp3": "sad violin",
    "04_modi_ji_rona_band_kijiye.mp3": "rona band kijiye",
    "05_faaah.mp3": "faaah fail",
    "01_hindi_guy_said_sorry.mp3": "sorry bhai",
    "02_uth_jaa.mp3": "uth jaa",
    "03_bhai_ne_bola_karnekka.mp3": "bhai ne bola",
    "01_shut_your_fckin_mouth.mp3": "shut your mouth",
    "02_you_shut_your_mouth_fatty.mp3": "shut up",
    "03_get_out_meme.mp3": "get out",
    "01_scout_yo_whats_up.mp3": "yo whats up",
    "02_what_39s_up_budweiser_commercial_mp3cut.mp3": "whats up",
    "03_quandale_dingle_v2.mp3": "quandale dingle",
    "04_ha_got_eeem.mp3": "ha got eem",
    "01_ny_video_online_audio_converter.mp3": "funny laugh",
    "02_ayooogima.mp3": "goofy laugh",
    "03_hi_hi_hi_ha_clash_royale.mp3": "heheheha",
    "01_tmp8ljn9e7h.mp3": "goodbye"
}

class MemeSoundEngine:
    """
    Meme Sound System for CZ AI Teammates.
    - Converts all sounds in `sounds/<tag>/` to 16-bit mono WAV at 22050 Hz
      and places them inside `czero/sound/ai_teammates/<tag>/` so the Condition Zero
      engine plays them natively via `client_cmd(0, "spk ...")`.
    - Does NOT use an external OS audio player.
    - Enforces anti-spam cooldowns (max 1 sound per 3s globally, same tag once per 8s).
    - Remembers last 3 files per tag (never repeats back-to-back).
    """
    def __init__(self, base_dir=None, enabled=True, volume=0.8, frequency="Normal", chat_style="full_gamer", subtitles_enabled=True, muted_bots=None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_dir = base_dir
        self.sounds_dir = os.path.join(self.base_dir, "sounds")
        self.cache_dir = os.path.join(self.sounds_dir, ".cache")
        self.czero_sound_dir = os.path.join(self.base_dir, "czero", "sound", "ai_teammates")
        self.manifest_path = os.path.join(self.sounds_dir, "manifest.json")

        self.enabled = enabled
        self.volume = max(0.0, min(1.0, float(volume)))
        self.frequency = frequency
        self.chat_style = chat_style.lower()
        self.subtitles_enabled = subtitles_enabled
        self.muted_bots = set([b.lower() for b in (muted_bots or [])])

        # External audio player kept disabled so sounds ONLY play inside the game engine
        self.player = AudioPlayer(external_enabled=False)
        self.player.set_volume(self.volume)

        # Cooldown & History tracking
        self.last_played_files = defaultdict(list)
        self.last_tag_time = {}
        self.last_global_time = 0.0
        self.empty_tags_warned = set()

        self.manifest = self._load_manifest()
        self.tag_files = {}
        self.cached_wav_paths = {}

        # Convert and install 16-bit mono 22050 Hz WAVs into czero/sound/ai_teammates/<tag>/
        self.scan_and_cache_sounds()

    def _load_manifest(self) -> dict:
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Sound] Warning loading manifest: {e}")
        return {"tags": {}}

    def scan_and_cache_sounds(self):
        """
        Scan all tag folders, convert audio to 16-bit 22050 Hz mono WAV,
        and place them into `czero/sound/ai_teammates/<tag>/` (and `sounds/.cache/<tag>/`).
        """
        self.tag_files = {}
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.czero_sound_dir, exist_ok=True)

        discovered_tags = set(KNOWN_TAGS)
        if "tags" in self.manifest:
            discovered_tags.update(self.manifest["tags"].keys())

        if os.path.exists(self.sounds_dir):
            for item in os.listdir(self.sounds_dir):
                full_p = os.path.join(self.sounds_dir, item)
                if os.path.isdir(full_p) and not item.startswith("."):
                    discovered_tags.add(item.lower())

        for tag in sorted(discovered_tags):
            tag_dir = os.path.join(self.sounds_dir, tag)
            tag_cache_dir = os.path.join(self.cache_dir, tag)
            tag_czero_dir = os.path.join(self.czero_sound_dir, tag)
            os.makedirs(tag_cache_dir, exist_ok=True)

            files = []
            if os.path.exists(tag_dir):
                files = [
                    f for f in os.listdir(tag_dir)
                    if f.lower().endswith((".mp3", ".wav"))
                ]

            self.tag_files[tag.lower()] = sorted(files)
            if files:
                os.makedirs(tag_czero_dir, exist_ok=True)

            for f in files:
                src_path = os.path.join(tag_dir, f)
                stem = os.path.splitext(f)[0]
                dst_cache_wav = os.path.join(tag_cache_dir, f"{stem}.wav")
                dst_czero_wav = os.path.join(tag_czero_dir, f"{stem}.wav")

                self._ensure_normalized_wav(src_path, dst_cache_wav)
                self._ensure_normalized_wav(src_path, dst_czero_wav)
                self.cached_wav_paths[(tag.lower(), f)] = dst_czero_wav

        print(f"[Sound] Loaded {sum(len(v) for v in self.tag_files.values())} sounds across {len(self.tag_files)} tags into czero/sound/ai_teammates/ (16-bit mono 22050 Hz WAV).")

    def _ensure_normalized_wav(self, src_path: str, dst_wav: str):
        """Convert & normalize to pure 44-byte header 16-bit 22050 Hz mono PCM WAV."""
        try:
            if os.path.exists(dst_wav) and os.path.getsize(dst_wav) > 44:
                if os.path.getmtime(dst_wav) >= os.path.getmtime(src_path):
                    return

            data, fs = sf.read(src_path, dtype='float32')
            if data.ndim > 1:
                mono = np.mean(data, axis=1)
            else:
                mono = data

            target_fs = 22050
            if fs != target_fs and len(mono) > 0:
                duration = len(mono) / fs
                new_len = max(1, int(duration * target_fs))
                mono = np.interp(
                    np.linspace(0, len(mono), new_len, endpoint=False),
                    np.arange(len(mono)),
                    mono
                )

            peak = np.max(np.abs(mono)) if len(mono) > 0 else 0
            if peak > 0.001:
                mono = mono * (0.75 / peak)

            pcm16 = np.clip(mono * 32767.0, -32768, 32767).astype(np.int16)
            with wave.open(dst_wav, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(target_fs)
                wf.writeframes(pcm16.tobytes())
        except Exception:
            pass

    def stop_all(self):
        """Immediately stop any pending audio and reset state."""
        self.player.stop_all()

    def set_settings(self, enabled=None, volume=None, frequency=None, chat_style=None, subtitles_enabled=None, muted_bots=None):
        if enabled is not None:
            self.enabled = bool(enabled)
        if volume is not None:
            self.volume = max(0.0, min(1.0, float(volume)))
            self.player.set_volume(self.volume)
        if frequency is not None:
            self.frequency = frequency
        if chat_style is not None:
            self.chat_style = chat_style.lower()
        if subtitles_enabled is not None:
            self.subtitles_enabled = bool(subtitles_enabled)
        if muted_bots is not None:
            self.muted_bots = set([b.lower() for b in muted_bots])

    def get_cooldowns(self) -> tuple[float, float]:
        """Returns (global_cooldown, tag_cooldown): max 1 sound per 3s, same tag once per 8s."""
        freq = self.frequency.capitalize()
        if freq == "Low":
            return (5.0, 12.0)
        return (3.0, 8.0)

    def can_play(self, tag: str, speaker_name: str = "", is_critical: bool = False) -> bool:
        if not self.enabled:
            return False

        tag = tag.lower()
        if speaker_name and speaker_name.lower() in self.muted_bots:
            return False

        if self.chat_style == "clean" and tag == "hindi_swear":
            return False

        now = time.time()
        if not is_critical:
            global_cd, tag_cd = self.get_cooldowns()
            if now - self.last_global_time < global_cd:
                return False
            if now - self.last_tag_time.get(tag, 0.0) < tag_cd:
                return False

        return True

    def get_tag_counts(self) -> dict[str, int]:
        result = {}
        for tag in KNOWN_TAGS:
            result[tag] = len(self.tag_files.get(tag, []))
        for tag, files in self.tag_files.items():
            if tag not in result:
                result[tag] = len(files)
        return result

    def get_friendly_name(self, filename: str) -> str:
        if filename in FRIENDLY_NAMES:
            return FRIENDLY_NAMES[filename]
        clean = os.path.splitext(filename)[0]
        clean = re.sub(r'^\d+[\s_-]*', '', clean)
        clean = clean.replace("_", " ").replace("-", " ")
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean or "sound"

    def play_tag(self, tag: str, speaker_name: str = "Teammate", pan: float = 0.0, is_critical: bool = False) -> tuple[str, str]:
        """
        Selects a sound for the given tag (never the same file twice in a row)
        and returns (subtitle_label, chosen_filename).
        Actual audio playback happens inside the Condition Zero engine via AMX Mod X `spk`.
        """
        tag = tag.lower()
        if not self.can_play(tag, speaker_name=speaker_name, is_critical=is_critical):
            return "", ""

        files = self.tag_files.get(tag, [])
        if not files:
            self.scan_and_cache_sounds()
            files = self.tag_files.get(tag, [])

        if not files:
            if tag not in self.empty_tags_warned:
                print(f"[Sound] Warning: Tag folder 'sounds/{tag}' is empty. Skipping sound.")
                self.empty_tags_warned.add(tag)
            return "", ""

        recent = self.last_played_files[tag]
        if len(files) == 1:
            chosen = files[0]
        elif len(files) <= 3:
            last_one = recent[-1] if recent else ""
            candidates = [f for f in files if f != last_one]
            chosen = random.choice(candidates if candidates else files)
        else:
            candidates = [f for f in files if f not in recent]
            if not candidates:
                candidates = [f for f in files if f != recent[-1]]
            chosen = random.choice(candidates if candidates else files)

        recent.append(chosen)
        if len(recent) > 3:
            recent.pop(0)

        now = time.time()
        self.last_tag_time[tag] = now
        self.last_global_time = now

        friendly = self.get_friendly_name(chosen)
        subtitle = f"*plays {friendly} [{tag}]*" if self.subtitles_enabled else ""
        print(f"[Sound] Selected '{chosen}' ({friendly} [{tag}]) for in-game playback [Speaker: {speaker_name}]")
        return subtitle, chosen
