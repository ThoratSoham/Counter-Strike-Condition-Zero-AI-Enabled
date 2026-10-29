import time
import random
import threading
from collections import deque
from brain.llm_client import LLMClient
from brain.offline_bank import get_offline_bank
from brain.logger import get_logger
from brain.safety_filter import is_safe_line

class ChatterEngine:
    """
    Manages bot-to-bot chatter, batch fetching, queues, argument/fight state machine,
    and real game event interruptions.
    Strictly gated on `self.game_connected`: NEVER creates chat or triggers sounds
    when the game is closed or disconnected.
    """
    def __init__(self, llm_client: LLMClient, dispatch_callback=None, chatter_speed="Very chatty", fight_frequency="Normal", chat_style="full_gamer"):
        self.llm_client = llm_client
        self.dispatch_callback = dispatch_callback
        self.chatter_speed = chatter_speed
        self.fight_frequency = fight_frequency
        self.chat_style = chat_style.lower()
        self.logger = get_logger()
        self.offline_bank = get_offline_bank()

        # Chatter Queue
        self.queue = deque()
        self._lock = threading.RLock()
        self.is_fetching = False

        # Game Connection Gate (False until game sends HEARTBEAT/PING)
        self.game_connected = False

        # Active game context
        self.game_context = {
            "map": "de_dust2",
            "round": 1,
            "alive_teammates": ["Vikram", "Kabir", "Marcus", "Sunny"],
            "last_events": ["Match warmup"]
        }
        self.mood_dict = {
            "vikram": {"tilt": 10, "stress": 20},
            "kabir": {"tilt": 5, "stress": 10},
            "marcus": {"tilt": 0, "stress": 15},
            "sunny": {"tilt": 5, "stress": 40}
        }
        self.recent_chat = []

        # Fight / Argument State Machine
        self.active_fight = {
            "active": False,
            "between": [],
            "stage": "none",
            "initiated_at": 0,
            "grudges": []
        }
        self.last_fight_time = time.time()

        # Loop control
        self.running = False
        self.worker_thread = None
        self.last_line_time = time.time()
        self.next_line_delay = self._sample_gap()

        # Event interruption
        self.urgent_event_pending = None
        self.current_reason = ""

    def start(self):
        if self.running:
            return
        self.running = True
        self.worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.worker_thread.start()
        self.logger.log(0, f"ChatterEngine initialized (Idle until game connects; Speed: {self.chatter_speed})")

    def stop(self):
        self.running = False
        self.pause_on_disconnect()

    def set_game_connected(self, connected: bool):
        """Enable or disable chatter generation based on live game heartbeat."""
        if connected and not self.game_connected:
            self.game_connected = True
            self.last_line_time = time.time()
            self.next_line_delay = self._sample_gap()
            self._refill_from_local_bank()
            self._check_and_refill_queue(async_refill=True)
            self.logger.log(0, "[Chatter] Game connected - chatter timer enabled.")
        elif not connected and self.game_connected:
            self.pause_on_disconnect()

    def pause_on_disconnect(self):
        """Immediately stop all timers, clear queue, and reset fights when game disconnects."""
        self.game_connected = False
        with self._lock:
            self.queue.clear()
            self.active_fight = {"active": False, "between": [], "stage": "none", "grudges": []}
            self.urgent_event_pending = None

    def update_game_context(self, context_update: dict):
        with self._lock:
            self.game_context.update(context_update)

    def record_game_event(self, event_str: str):
        with self._lock:
            events = self.game_context.setdefault("last_events", [])
            events.append(event_str)
            if len(events) > 5:
                events.pop(0)

    def set_settings(self, chatter_speed=None, fight_frequency=None, chat_style=None):
        with self._lock:
            if chatter_speed:
                self.chatter_speed = chatter_speed
            if fight_frequency:
                self.fight_frequency = fight_frequency
            if chat_style:
                self.chat_style = chat_style.lower()

    def _sample_gap(self) -> float:
        """Sample idle gap based on chatter_speed setting."""
        speed = self.chatter_speed.capitalize()
        if self.active_fight.get("active"):
            return random.uniform(3.0, 6.0)

        if speed == "Relaxed":
            return random.uniform(25.0, 40.0)
        elif speed == "Normal":
            return random.uniform(15.0, 25.0)
        return random.uniform(10.0, 20.0)

    def _should_trigger_random_fight(self) -> bool:
        if not self.game_connected:
            return False
        if self.fight_frequency == "Off":
            return False
        if self.active_fight.get("active"):
            return False

        now = time.time()
        min_cooldown = 120.0 if self.fight_frequency == "Often" else 200.0
        if now - self.last_fight_time < min_cooldown:
            return False

        chance = 0.40 if self.fight_frequency == "Often" else 0.20
        return random.random() < chance

    def trigger_fight(self, bot_a="Vikram", bot_b="Kabir", trigger_reason=""):
        """Initiate a heated bot-to-bot argument."""
        with self._lock:
            self.active_fight = {
                "active": True,
                "between": [bot_a, bot_b],
                "stage": "start",
                "initiated_at": time.time(),
                "grudges": self.active_fight.get("grudges", [])
            }
            self.last_fight_time = time.time()

        clean_mode = (self.chat_style == "clean")
        fight_script, fight_meta = self.offline_bank.generate_fight_script(bot_a, bot_b, clean_mode=clean_mode)

        with self._lock:
            for line in reversed(fight_script):
                line["reason"] = f"triggered by {bot_a} vs {bot_b} fight"
                self.queue.appendleft(line)

        self.logger.log(0, f"[Chatter] Bot fight started between {bot_a} and {bot_b}! ({trigger_reason or 'banter'})")

    def force_fight(self):
        """Console command 'ai_force_fight'."""
        bots = ["Vikram", "Kabir", "Marcus", "Sunny"]
        pair = random.sample(bots, 2)
        self.trigger_fight(pair[0], pair[1], trigger_reason="ai_force_fight command")

    def force_chat(self):
        """Console command 'ai_force_chat' to play next line immediately."""
        if not self.game_connected:
            return
        line = None
        with self._lock:
            if not self.queue:
                self._refill_from_local_bank()
            if self.queue:
                line = self.queue.popleft()
                self.last_line_time = time.time()
                self.next_line_delay = self._sample_gap()
        if line:
            self._dispatch(line)

    def reset_queue_and_memory(self):
        """Console command 'ai_reset'."""
        with self._lock:
            self.queue.clear()
            self.active_fight = {"active": False, "between": [], "stage": "none", "grudges": []}
            self.recent_chat.clear()
        self.logger.log(0, "[Chatter] Queue and fight memory reset.")
        if self.game_connected:
            self._refill_from_local_bank()
            self._check_and_refill_queue(async_refill=True)

    def interrupt_with_event(self, bot_id: str, event_type: str, details: dict = None):
        """
        Real game events (kill, death, bomb, round end) cut the idle script,
        and make the right bot react within 1 to 2 seconds!
        """
        if not self.game_connected:
            return

        clean_mode = (self.chat_style == "clean")
        text, tag, mood = self.offline_bank.get_event_reaction(event_type, bot_id, clean_mode=clean_mode)
        if not tag:
            default_event_tags = {
                "death": "fail_sad",
                "kill": "headshot" if (details and details.get("headshot")) else "hype",
                "bomb_planted": "shock",
                "bomb_defused": "hype",
                "bomb_exploded": "shock",
                "round_win": "hype",
                "round_loss": "fail_sad",
            }
            tag = default_event_tags.get(event_type, "fail_sad")

        speaker = bot_id.capitalize()
        for b in ["Vikram", "Kabir", "Marcus", "Sunny"]:
            if b.lower() == bot_id.lower():
                speaker = b
                break

        event_reasons = {
            "kill": "triggered by headshot kill" if (details and details.get("headshot")) else "triggered by kill",
            "death": f"triggered by {details.get('victim', 'teammate')}'s death" if details else "triggered by death",
            "bomb_planted": "triggered by bomb plant",
            "bomb_defused": "triggered by bomb defuse",
            "bomb_exploded": "triggered by bomb explosion",
            "round_win": "triggered by round win",
            "round_loss": "triggered by round loss",
        }
        line = {
            "speaker": speaker,
            "text": text,
            "sound_tag": tag,
            "delay_ms": 1200,
            "mood": mood,
            "is_event": True,
            "reason": event_reasons.get(event_type, f"triggered by {event_type}")
        }

        def _dispatch_event():
            time.sleep(random.uniform(0.8, 1.5))
            if not self.game_connected or not self.running:
                return
            self._dispatch(line, is_critical=True)
            self.last_line_time = time.time()
            self.next_line_delay = self._sample_gap()

        threading.Thread(target=_dispatch_event, daemon=True).start()

    def _check_and_refill_queue(self, async_refill=True):
        with self._lock:
            if len(self.queue) > 3 or self.is_fetching:
                return
            self.is_fetching = True

        def _worker():
            try:
                batch_script, fight_meta, ok, err = self.llm_client.generate_batch_script(
                    game_context=self.game_context,
                    mood_dict=self.mood_dict,
                    recent_chat=self.recent_chat,
                    active_fight=self.active_fight,
                    batch_size=10
                )

                if ok and batch_script:
                    with self._lock:
                        for line in batch_script:
                            # Idle lines do not play standalone timer sounds unless part of an active fight
                            if not self.active_fight.get("active"):
                                line["sound_tag"] = ""
                            self.queue.append(line)
                        if fight_meta and fight_meta.get("active"):
                            self.active_fight = fight_meta
                    return

                self._refill_from_local_bank()
            finally:
                with self._lock:
                    self.is_fetching = False

        if async_refill:
            threading.Thread(target=_worker, daemon=True).start()
        else:
            _worker()

    def _refill_from_local_bank(self):
        clean_mode = (self.chat_style == "clean")
        script = self.offline_bank.generate_idle_script(
            active_bots=self.game_context.get("alive_teammates", ["Vikram", "Kabir", "Marcus", "Sunny"]),
            size=10,
            clean_mode=clean_mode
        )
        with self._lock:
            for line in script:
                # Idle chatter lines show chat in-game without firing random timer sounds
                if not self.active_fight.get("active"):
                    line = dict(line)
                    line["sound_tag"] = ""
                self.queue.append(line)

    def _dispatch(self, line: dict, is_critical=False):
        if not self.game_connected:
            return

        speaker = line.get("speaker", "Vikram")
        text = line.get("text", "")
        sound_tag = line.get("sound_tag") or ""
        mood = line.get("mood", "neutral")

        safe, reason = is_safe_line(text)
        if not safe:
            self.logger.log(0, f"[Safety] Filtered unsafe line: {reason}")
            return

        self.recent_chat.append(f"{speaker}: {text}")
        if len(self.recent_chat) > 15:
            self.recent_chat.pop(0)

        if self.dispatch_callback:
            self.current_reason = line.get("reason", "bot banter")
            self.dispatch_callback(speaker, text, sound_tag, mood, is_critical=is_critical)

    def _run_loop(self):
        """Continuous background loop driving bot chatter ONLY when game is connected."""
        while self.running:
            try:
                time.sleep(0.5)

                # Strict Step 2 Gate: Never run timers, fetch lines, or play sounds when game is not connected
                if not self.game_connected:
                    continue

                now = time.time()
                self._check_and_refill_queue(async_refill=True)

                if self._should_trigger_random_fight():
                    bots = ["Vikram", "Kabir", "Marcus", "Sunny"]
                    p = random.sample(bots, 2)
                    self.trigger_fight(p[0], p[1], trigger_reason="random match event")

                if now - self.last_line_time >= self.next_line_delay:
                    line = None
                    with self._lock:
                        if self.queue:
                            line = self.queue.popleft()

                    if line and self.game_connected:
                        delay_ms = line.get("delay_ms", 1500)
                        time.sleep(delay_ms / 1000.0)
                        if not self.game_connected or not self.running:
                            continue

                        self._dispatch(line)
                        self.last_line_time = time.time()
                        self.next_line_delay = self._sample_gap()
            except Exception:
                time.sleep(1.0)

    def get_status(self) -> dict:
        with self._lock:
            q_size = len(self.queue)
            fight_desc = "None"
            if self.active_fight.get("active"):
                fight_desc = f"{' vs '.join(self.active_fight.get('between', []))} [{self.active_fight.get('stage', 'rising')}]"
            elif self.active_fight.get("grudges"):
                fight_desc = f"Cooling down ({', '.join(self.active_fight.get('grudges', [])[-1:])})"

        return {
            "game_connected": self.game_connected,
            "queue_size": q_size,
            "fight_state": fight_desc,
            "chatter_speed": self.chatter_speed,
            "fight_frequency": self.fight_frequency,
            "chat_style": self.chat_style,
            "recent_chat_count": len(self.recent_chat),
            "is_fetching": self.is_fetching
        }
