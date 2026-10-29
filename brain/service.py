import os
import json
import time
import random
import ctypes
import threading
from ctypes import wintypes
from plugin.game_bridge import GameBridge
from plugin.rcon import GoldSrcRcon
from voice.meme_player import MemeSoundEngine
from voice.engine import VoiceEngine
from stt.listener import SpeechToTextListener
from brain.mood import MoodManager
from brain.memory import MemoryManager
from brain.budget import TalkBudgetManager
from brain.llm_client import LLMClient
from brain.chatter_engine import ChatterEngine
from brain.offline_bank import get_offline_bank
from brain.logger import get_logger

def is_hl_process_running() -> bool:
    """
    Fast Win32 Toolhelp32 snapshot check (~0.2ms, zero subprocesses)
    to detect if Condition Zero (`hl.exe` / `czero.exe` / `cstrike.exe`) is running.
    """
    if os.name != "nt":
        return False
    try:
        TH32CS_SNAPPROCESS = 0x00000002
        class PROCESSENTRY32(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", wintypes.LONG),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", ctypes.c_char * 260),
            ]

        kernel32 = ctypes.windll.kernel32
        snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snap == -1:
            return False
        try:
            pe = PROCESSENTRY32()
            pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
            if not kernel32.Process32First(snap, ctypes.byref(pe)):
                return False
            while True:
                exe = pe.szExeFile.decode("latin-1", errors="ignore").lower()
                if exe in ("hl.exe", "czero.exe", "cstrike.exe"):
                    return True
                if not kernel32.Process32Next(snap, ctypes.byref(pe)):
                    break
        finally:
            kernel32.CloseHandle(snap)
    except Exception:
        pass
    return False


class AIBrainService:
    """
    Core AI Brain Service for CZ AI Teammates.
    - Strictly gated on game connection: NEVER creates chat or plays sounds when game is closed.
    - Tracks 2s plugin heartbeat; if no heartbeat for 10s, stops all timers, clears queue, stops audio, and idles.
    - Watches `hl.exe` process; when the game closes, shuts down fully within 5 seconds.
    - Sends only sound TAGs to the in-game AMX Mod X plugin so the GoldSrc engine plays WAVs natively.
    """
    HEARTBEAT_TIMEOUT_SEC = 10.0

    def __init__(self, config_path=None, exit_on_game_close=False):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        self.config_path = config_path
        self.config = self._load_config()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.logger = get_logger()
        self.exit_on_game_close = exit_on_game_close

        self.teammates = self.config.get("active_teammates", ["vikram", "kabir", "marcus", "sunny"])
        self.teammates_cased = ["Vikram", "Kabir", "Marcus", "Sunny"]

        self.chat_style = self.config.get("chat_style", "full_gamer")
        self.chatter_speed = self.config.get("chatter_speed", "Very chatty")
        self.fight_frequency = self.config.get("fight_frequency", "Normal")
        self.subtitles_enabled = self.config.get("subtitles_enabled", True)
        self.muted_bots = self.config.get("muted_bots", [])

        # Meme Sound System (prepares 16-bit 22050 Hz mono WAVs in czero/sound/ai_teammates/<tag>/)
        self.meme_sound = MemeSoundEngine(
            base_dir=self.base_dir,
            enabled=self.config.get("sounds_enabled", True),
            volume=self.config.get("sound_volume", 0.8),
            frequency=self.config.get("sound_frequency", "Normal"),
            chat_style=self.chat_style,
            subtitles_enabled=self.subtitles_enabled,
            muted_bots=self.muted_bots
        )

        self.voice_engine = VoiceEngine(
            base_dir=self.base_dir,
            language=self.config.get("language", "en"),
            volume=self.config.get("voice_volume", 1.0),
            spatial=self.config.get("spatial_audio", True)
        )

        self.rcon = GoldSrcRcon(
            host=self.config.get("server_host", "127.0.0.1"),
            port=self.config.get("server_port", 27015),
            password=self.config.get("rcon_password", "czeroai")
        )
        self.mood_manager = MoodManager(self.voice_engine.personalities)
        self.memory_manager = MemoryManager()
        self.budget_manager = TalkBudgetManager(daily_limit=self.config.get("talk_budget_daily_limit", 500))

        self.llm_client = LLMClient(
            provider=self.config.get("llm_provider", "gemini"),
            google_api_key=self.config.get("google_api_key", ""),
            gemini_api_key=self.config.get("gemini_api_key", ""),
            model_name=self.config.get("gemini_model", "gemini-2.5-flash"),
            chat_style=self.chat_style,
            language=self.config.get("language", "en")
        )

        self.chatter_engine = ChatterEngine(
            llm_client=self.llm_client,
            dispatch_callback=self.dispatch_bot_line,
            chatter_speed=self.chatter_speed,
            fight_frequency=self.fight_frequency,
            chat_style=self.chat_style
        )

        self.stt_listener = SpeechToTextListener(
            key=self.config.get("push_to_talk_key", "v"),
            model_name=self.config.get("whisper_model", "tiny.en"),
            on_transcription=self.handle_player_message
        )

        self.game_bridge = GameBridge(
            host=self.config.get("server_host", "127.0.0.1"),
            port=self.config.get("log_listener_port", 27115),
            event_handler=self.handle_game_event
        )

        self.running = False
        self.shutdown_requested = False
        self.hl_process_seen = is_hl_process_running()
        self.watchdog_thread = None
        self.last_event_time = 0.0
        self.last_kill_react_time = 0.0
        self.last_round_start_time = 0.0

    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def is_game_connected(self) -> bool:
        """Returns True ONLY when the in-game plugin has sent a heartbeat within the last 10 seconds."""
        if not self.game_bridge.is_connected:
            return False
        if time.time() - self.game_bridge.last_heartbeat > self.HEARTBEAT_TIMEOUT_SEC:
            return False
        return True

    def start(self):
        if self.running:
            return
        self.running = True
        self.shutdown_requested = False
        self.hl_process_seen = is_hl_process_running()

        self.logger.log(0, "Starting AI Teammates Brain Service (Idle until game connects)...")
        self.game_bridge.start()
        self.stt_listener.start_listening()
        self.chatter_engine.start()

        self.watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self.watchdog_thread.start()
        self.logger.log(0, "AI Teammates Brain Service ready and waiting for game heartbeat.")

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.logger.log(0, "Stopping AI Teammates Brain Service...")
        self.disconnect_and_idle("Service stopping")
        self.chatter_engine.stop()
        self.game_bridge.stop()
        self.stt_listener.stop_listening()

    def disconnect_and_idle(self, reason: str = ""):
        """
        Immediately stop all timers, clear chatter queue, stop all audio,
        and mark the game disconnected.
        """
        self.game_bridge.mark_disconnected()
        self.chatter_engine.pause_on_disconnect()
        self.meme_sound.stop_all()
        if hasattr(self.voice_engine, "player"):
            self.voice_engine.player.stop_all()
        if reason:
            self.logger.log(0, f"[Brain] Game disconnected ({reason}) — stopped timers, cleared queue, stopped audio.")

    def _watchdog_loop(self):
        """
        Checks every 0.5s:
        1. Heartbeat timeout (10s without heartbeat -> stop timers, clear queue, stop audio, go idle).
        2. Game process watcher (`hl.exe` closes -> stop everything and shut down within < 5s).
        """
        while self.running:
            try:
                time.sleep(0.5)
                now = time.time()

                # 1. Watch `hl.exe` process (with a 2.0s grace check for Half-Life -> "Change Game" -> czero restart)
                hl_alive = is_hl_process_running()
                if hl_alive and not self.hl_process_seen:
                    self.hl_process_seen = True
                    self.logger.log(0, "[Brain] Detected hl.exe (Condition Zero) process running.")
                elif self.hl_process_seen and not hl_alive:
                    # Wait up to 2.0s in case hl.exe is restarting from "Change Game -> Condition Zero"
                    restarted = False
                    for _ in range(4):
                        time.sleep(0.5)
                        if is_hl_process_running():
                            restarted = True
                            break
                    if not restarted:
                        self.hl_process_seen = False
                        self.disconnect_and_idle("hl.exe process closed")
                        if self.exit_on_game_close:
                            self.logger.log(0, "[Brain] hl.exe closed — shutting down Brain Service now.")
                            self.shutdown_requested = True
                            self.stop()
                            return

                # 2. Check 10-second heartbeat timeout
                if self.game_bridge.is_connected:
                    elapsed = now - self.game_bridge.last_heartbeat
                    if elapsed > self.HEARTBEAT_TIMEOUT_SEC:
                        self.disconnect_and_idle(f"No heartbeat for {elapsed:.1f}s")
                        if self.exit_on_game_close and not hl_alive:
                            self.shutdown_requested = True
                            self.stop()
                            return
            except Exception:
                pass

    def sync_status_to_plugin(self):
        if not self.is_game_connected():
            return
        provider_label = f"AI Studio ({self.llm_client.model_name})" if self.llm_client.is_online() else "Offline (Local Bank)"
        req_left = max(0, self.budget_manager.daily_limit - self.llm_client.daily_requests)
        chatter_status = self.chatter_engine.get_status()

        q_size = chatter_status.get("queue_size", 0)
        fight_state = chatter_status.get("fight_state", "None")
        speed = chatter_status.get("chatter_speed", "Very chatty")
        fight_freq = chatter_status.get("fight_frequency", "Normal")
        style = chatter_status.get("chat_style", "full_gamer")

        packet = f"STATUS|{provider_label}|{req_left}|{q_size}|{fight_state}|{speed}|{fight_freq}|{style}"
        self.game_bridge.send_to_plugin(packet)

    def dispatch_bot_line(self, speaker: str, text: str, sound_tag: str = "", mood: str = "neutral", is_critical: bool = False, reason: str = ""):
        """
        Sends chat line and optional sound TAG to the in-game AMX Mod X plugin.
        Strictly gated: NEVER creates chat or plays sounds when the game is not connected.
        """
        if not self.is_game_connected():
            return

        if not reason:
            reason = getattr(self.chatter_engine, "current_reason", "") or "bot banter"

        # Step 4: Send ONLY the sound TAG to the plugin; the plugin picks a random WAV and plays it in-game!
        if sound_tag:
            sound_label, chosen_file = self.meme_sound.play_tag(
                sound_tag,
                speaker_name=speaker,
                is_critical=is_critical
            )
            if sound_label:
                self.logger.log(7, f"Sound tag dispatched to game: '{sound_tag}' (Speaker: {speaker}, Reason: {reason})")
                self.game_bridge.send_to_plugin(f"SOUND|{speaker}|{sound_tag}|{reason}")

        # Send chat line to AMX Mod X plugin
        self.game_bridge.send_to_plugin(f"SAY|{speaker}|{text}")
        self.logger.log(6, f"Chat message sent into the game as a bot: [{speaker}] {text}")

        self.sync_status_to_plugin()

    def handle_game_event(self, event_name: str, data: dict):
        if event_name == "game_connected":
            self.chatter_engine.set_game_connected(True)
            return

        if event_name == "game_disconnected":
            reason = data.get("reason", "disconnected")
            self.disconnect_and_idle(reason)
            if self.exit_on_game_close:
                self.shutdown_requested = True
                self.stop()
            return

        # All other events ensure chatter engine is marked connected
        if not self.chatter_engine.game_connected:
            self.chatter_engine.set_game_connected(True)
        self.sync_status_to_plugin()

        if event_name == "force_fight":
            self.chatter_engine.force_fight()
            return

        if event_name == "force_chat":
            self.chatter_engine.force_chat()
            return

        if event_name == "reset":
            self.chatter_engine.reset_queue_and_memory()
            return

        if event_name == "test_sound":
            tag = data.get("tag", "hype")
            requester = data.get("requester", "")
            reason = data.get("reason", f"command ai_test_sound {tag}")
            self.logger.log(7, f"Sound test requested for tag '{tag}' by '{requester or 'console'}' ({reason})")
            bot = requester if requester else random.choice(self.teammates_cased)
            sound_label, chosen_file = self.meme_sound.play_tag(tag, speaker_name=bot, is_critical=True)
            if sound_label:
                self.game_bridge.send_to_plugin(f"SOUND|{bot}|{tag}|{reason}")
                self.game_bridge.send_to_plugin(f"SAY|{bot}|[Testing {tag} sound]")
            return

        if event_name == "chat":
            sender = data.get("sender", "Player")
            msg = data.get("message", "")
            if any(t in sender.lower() for t in self.teammates) or msg.startswith("[") or msg.startswith("*plays "):
                return
            self.handle_player_message(msg, sender=sender)
            return

        self.chatter_engine.record_game_event(f"Event: {event_name}")

        if event_name == "kill":
            attacker = data.get("attacker", "")
            victim = data.get("victim", "")
            headshot = data.get("headshot", False)

            for t_id in self.teammates:
                if t_id in attacker.lower():
                    self.mood_manager.update_on_kill(t_id, is_headshot=headshot)
                    self.chatter_engine.interrupt_with_event(t_id, "kill", {"headshot": headshot})
                    return

            for t_id in self.teammates:
                if t_id in victim.lower():
                    self.mood_manager.update_on_death(t_id, is_headshot=headshot)
                    living = [t for t in self.teammates if t != t_id]
                    reactor = random.choice(living) if living else "vikram"
                    self.chatter_engine.interrupt_with_event(reactor, "death", {"victim": t_id})
                    return

            # Also react when standard Condition Zero bots (e.g. Opie, Frank, Harold) or Player die/kill
            now = time.time()
            if now - self.last_kill_react_time >= 4.0:
                self.last_kill_react_time = now
                reactor = random.choice(self.teammates)
                if victim and victim.lower() != "world":
                    self.chatter_engine.interrupt_with_event(reactor, "death", {"victim": victim})
                else:
                    self.chatter_engine.interrupt_with_event(reactor, "kill", {"headshot": headshot})
                return

        elif event_name == "bomb_planted":
            caller = random.choice(["vikram", "marcus", "sunny"])
            self.chatter_engine.interrupt_with_event(caller, "bomb_planted")

        elif event_name == "bomb_defused":
            caller = random.choice(self.teammates)
            self.chatter_engine.interrupt_with_event(caller, "bomb_defused")

        elif event_name == "bomb_exploded":
            caller = random.choice(["vikram", "kabir", "sunny"])
            self.chatter_engine.interrupt_with_event(caller, "bomb_exploded")

        elif event_name == "round_start":
            now = time.time()
            if now - self.last_round_start_time >= 6.0:
                self.last_round_start_time = now
                caller = random.choice(self.teammates)
                self.dispatch_bot_line(caller.capitalize(), "Round start! Let's get these frags!", sound_tag="greeting", reason="triggered by round start")

        elif event_name == "round_end":
            won = data.get("won", True)
            self.memory_manager.record_match_end(won=won)
            if won:
                self.mood_manager.update_on_round_win()
                caller = random.choice(self.teammates)
                self.chatter_engine.interrupt_with_event(caller, "round_win")
            else:
                self.mood_manager.update_on_round_loss()
                caller = random.choice(["vikram", "kabir", "sunny"])
                self.chatter_engine.interrupt_with_event(caller, "round_loss")

    def handle_player_message(self, message: str, sender: str = "Player"):
        """Process player message from say/say_team or push-to-talk mic (only when game is connected)."""
        if not self.is_game_connected():
            return

        msg_lower = message.lower()

        target_id = "vikram"
        for t in self.teammates:
            if t in msg_lower:
                target_id = t
                break
        else:
            target_id = random.choice(self.teammates)

        pers = self.voice_engine.get_personality(target_id)
        mood = self.mood_manager.get_mood(target_id)
        speaker = pers.get("name", target_id.capitalize())

        reply_text = ""
        emotion_tag = ""
        if self.llm_client.is_online():
            reply_text, emotion_tag, ok = self.llm_client.generate_single_reply(pers, message, {}, mood)

        if not reply_text:
            clean_mode = (self.chat_style == "clean")
            reply_text, emotion_tag, _ = get_offline_bank().get_line(target_id, "idle_chat", clean_mode=clean_mode)

        self.dispatch_bot_line(speaker, reply_text, sound_tag=emotion_tag, is_critical=True, reason=f"reply to {sender}")
