import os
import requests
import json
import re
import time
from brain.logger import get_logger
from brain.safety_filter import is_safe_line

KNOWN_TAGS = [
    "hype", "kill_headshot", "shock", "praise", "roast",
    "hindi_swear", "fail_sad", "apology_getup", "shut_up",
    "greeting", "laugh", "goodbye"
]

class LLMClient:
    """
    Connects to Google AI Studio (Gemini) API to generate batch chatter and replies.
    Features:
    - Reads Google AI Studio key from config.json or GOOGLE_API_KEY environment variable.
    - Never hardcodes or logs keys.
    - Free and fast flash-class model (default gemini-2.5-flash).
    - Batch generation returning 8 to 12 lines formatted as strict JSON.
    - Full retry logic and validation.
    - Logs every AI call with model, latency, tokens, and errors.
    - Logs '[AI] offline: <reason>' once on failure.
    """
    def __init__(self, provider="gemini", google_api_key="", gemini_api_key="", model_name="gemini-2.5-flash", chat_style="full_gamer", language="en"):
        self.provider = provider
        self.model_name = model_name or "gemini-2.5-flash"
        self.chat_style = chat_style.lower()
        self.language = language
        self.logger = get_logger()
        self.offline_warned = False

        # Resolve API Key securely
        self.google_api_key = self._resolve_api_key(google_api_key, gemini_api_key)

        # Rate limiting metrics
        self.request_times = [] # timestamps for RPM
        self.daily_requests = 0

    def _resolve_api_key(self, google_api_key: str, gemini_api_key: str) -> str:
        key = (google_api_key or "").strip()
        if not key:
            key = os.environ.get("GOOGLE_API_KEY", "").strip()
        if not key:
            key = (gemini_api_key or "").strip()
        return key

    def set_key(self, key: str):
        self.google_api_key = (key or "").strip()
        self.offline_warned = False

    def set_model(self, model: str):
        if model:
            self.model_name = model.strip()

    def set_chat_style(self, style: str):
        self.chat_style = style.lower()

    def record_request(self):
        now = time.time()
        self.request_times.append(now)
        # Prune older than 60s
        self.request_times = [t for t in self.request_times if now - t < 60.0]
        self.daily_requests += 1

    def get_requests_per_minute(self) -> int:
        now = time.time()
        self.request_times = [t for t in self.request_times if now - t < 60.0]
        return len(self.request_times)

    def is_online(self) -> bool:
        return bool(self.google_api_key)

    def _build_batch_system_prompt(self, game_context: dict, mood_dict: dict, recent_chat: list, active_fight: dict = None) -> str:
        style_desc = (
            "Authentic gamer banter between friends with light to moderate swearing (damn, shit, fuck, hell, bruh, clown). "
            "STRICT HARD LIMITS: Absolute zero tolerance for racial, religious, or identity slurs, hate speech, or real-world threats. "
            "All roasts and arguments must feel like passionate gamer friends teasing each other in a tactical shooter."
        )
        if self.chat_style == "clean":
            style_desc = "Clean family-friendly banter. No swear words, no slurs, no hindi_swear tags."
        elif self.chat_style == "banter":
            style_desc = "Mild playful banter with light gamer slang and minimal swearing. Strict no slurs or hate speech."

        active_fight_str = "None"
        if active_fight and active_fight.get("active"):
            active_fight_str = f"Active fight between {active_fight.get('between', [])} at stage '{active_fight.get('stage', 'rising')}'"

        prompt = f"""You are the AI scriptwriter for 4 bot teammates in Counter-Strike: Condition Zero (GoldSrc engine).
The human player is the audience watching these 4 friends talk non-stop in team chat.

THE 4 PERSONALITIES (Keep them distinct and consistent):
- Vikram (The Hothead): Loud, aggressive, rages fast, blames everyone, CAPS when angry, entry fragger.
- Kabir (The Jokester): Roasts everyone, makes puns, fake excuses ("my ping is 900", "my mom is calling"), loves memes.
- Marcus (The Calm Pro): Veteran sniper, dry humor, short lines (2-8 words), savage one-liners, rarely swears.
- Sunny (The Newbie): Nervous, asks silly questions ("should I buy P90?"), gets teased but barks back, screams in shock.

CURRENT MATCH CONTEXT:
- Map: {game_context.get('map', 'de_dust2')}
- Score/Round: Round {game_context.get('round', 1)}
- Alive teammates: {', '.join(game_context.get('alive_teammates', ['Vikram', 'Kabir', 'Marcus', 'Sunny']))}
- Last 5 events: {json.dumps(game_context.get('last_events', ['Round starting']))}
- Recent chat (last 5 lines): {json.dumps(recent_chat[-5:] if recent_chat else [])}
- Active fight state: {active_fight_str}
- Moods: {json.dumps(mood_dict)}
- Chat Style: {style_desc}

VALID SOUND TAGS:
{json.dumps(KNOWN_TAGS)}

RULES FOR GENERATED LINES:
1. Generate between 8 and 12 lines of dialogue between the bots.
2. Group the lines into 2 to 3 multi-turn conversational exchanges (where bots TALK TO EACH OTHER, reply to each other, roast each other, or argue about weapons/tactics). NEVER output random disconnected single sentences!
3. Each line must be 2 to 14 words. Authentic gamer slang, funny banter, small typos sometimes, NO long speeches.
4. sound_tag MUST BE PRECISE AND CONTEXTUAL. Only attach a sound_tag when it fits the exact emotional punchline of the line (~1 in 3 lines):
   - 'kill_headshot': ONLY when celebrating a headshot kill or crisp shot.
   - 'roast': ONLY when delivering a sharp roast or mocking a teammate's aim/play.
   - 'fail_sad': ONLY when failing, missing, or lamenting a death.
   - 'shock': ONLY on sudden surprise, screaming, panic, or bomb timer.
   - 'shut_up': ONLY when telling a teammate to quiet down or stop whining.
   - 'laugh': ONLY when laughing at something genuinely funny.
   - 'hype': ONLY on aggressive rush calls or big hype moments.
   - 'praise': ONLY when complimenting a good teammate play.
   - 'apology_getup': ONLY when apologizing after a fight.
   - Set sound_tag to null or "" for normal sentences! NEVER attach a random, unrelated sound tag!
5. delay_ms: between 1200 and 2400 (natural typing delay).
6. Fights: If an argument occurs or is active, have two bots argue through stages (start -> rising -> peak -> cool down/make up). Other bots may tell them to shut up.
7. OUTPUT FORMAT: Return STRICT JSON ONLY matching this exact schema:
{{
  "script": [
    {{"speaker": "Vikram", "text": "bro who taught you to aim, a toaster?", "sound_tag": "roast", "delay_ms": 1800, "mood": "annoyed"}},
    {{"speaker": "Kabir", "text": "lmaooo my cat walked on the mouse", "sound_tag": "laugh", "delay_ms": 1400, "mood": "amused"}}
  ],
  "fight": {{"active": false, "between": [], "stage": "none"}}
}}
"""
        return prompt

    def generate_batch_script(self, game_context: dict, mood_dict: dict, recent_chat: list, active_fight: dict = None, batch_size: int = 10) -> tuple[list[dict], dict, bool, str]:
        """
        Generate a batch of 8 to 12 chat lines as strict JSON from Google AI Studio.
        Returns: (script_list, fight_meta, is_success, error_or_reason)
        """
        if not self.google_api_key:
            if not self.offline_warned:
                self.logger.log_offline("No Google AI key configured in config.json or environment. Using Local Bank.")
                self.offline_warned = True
            return [], {}, False, "No Google AI key configured"

        # Check RPM limits (free tier is 15 RPM)
        if self.get_requests_per_minute() >= 12:
            return [], {}, False, "Approaching RPM limit (slow down to preserve quota)"

        start_time = time.time()
        self.record_request()
        self.logger.log(4, f"AI API called: {self.model_name} via Google AI Studio (Tokens: est ~350, Batch: {batch_size})")

        sys_prompt = self._build_batch_system_prompt(game_context, mood_dict, recent_chat, active_fight)
        user_prompt = f"Write the next batch of {batch_size} bot chat lines now in strict JSON format:"

        # Attempt call (with 1 retry on broken JSON or timeout)
        for attempt in range(2):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.google_api_key}"
                payload = {
                    "contents": [
                        {"role": "user", "parts": [{"text": f"{sys_prompt}\n\n{user_prompt}"}]}
                    ],
                    "generationConfig": {
                        "temperature": 0.88,
                        "maxOutputTokens": 800,
                        "responseMimeType": "application/json"
                    }
                }
                resp = requests.post(url, json=payload, timeout=10.0)
                duration_ms = int((time.time() - start_time) * 1000)

                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        continue
                    raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                    parsed_script, parsed_fight = self._parse_json_response(raw_text)

                    if parsed_script:
                        # Safety check each line
                        safe_script = []
                        for item in parsed_script:
                            safe, _ = is_safe_line(item.get("text", ""))
                            if safe:
                                safe_script.append(item)

                        if safe_script:
                            self.offline_warned = False
                            self.logger.log(5, f"AI answer received from {self.model_name} in {duration_ms}ms ({len(safe_script)} lines generated)")
                            return safe_script, parsed_fight, True, ""
                    # If JSON parsing failed on attempt 0, loop to retry once
                elif resp.status_code == 429:
                    err = "HTTP 429 Rate Limit / Daily Quota Exceeded"
                    self.logger.log(5, f"AI API failed after {duration_ms}ms: {err}")
                    if not self.offline_warned:
                        self.logger.log_offline(err)
                        self.offline_warned = True
                    return [], {}, False, err
                elif resp.status_code in [400, 403]:
                    err = f"HTTP {resp.status_code} Invalid API Key / Permissions"
                    self.logger.log(5, f"AI API failed after {duration_ms}ms: {err}")
                    if not self.offline_warned:
                        self.logger.log_offline(err)
                        self.offline_warned = True
                    return [], {}, False, err
                else:
                    err = f"HTTP {resp.status_code}: {resp.text[:120]}"
                    self.logger.log(5, f"AI API failed after {duration_ms}ms: {err}")
            except requests.exceptions.Timeout:
                duration_ms = int((time.time() - start_time) * 1000)
                self.logger.log(5, f"AI API timeout after {duration_ms}ms (Attempt {attempt+1})")
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                self.logger.log(5, f"AI API exception after {duration_ms}ms: {e}")

        # Both attempts failed
        if not self.offline_warned:
            self.logger.log_offline(f"{self.model_name} unavailable. Switching to Local Bank.")
            self.offline_warned = True
        return [], {}, False, "Failed after 2 attempts"

    def _parse_json_response(self, text: str) -> tuple[list[dict], dict]:
        """Parse and validate strict JSON response."""
        try:
            # Strip markdown code blocks if present
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)
            data = json.loads(cleaned)
            script = data.get("script", [])
            fight = data.get("fight", {})

            validated_script = []
            valid_speakers = ["vikram", "kabir", "marcus", "sunny"]

            for line in script:
                speaker = line.get("speaker", "Vikram").strip()
                # Normalize speaker name capitalization
                matched_speaker = speaker.capitalize()
                for v in ["Vikram", "Kabir", "Marcus", "Sunny"]:
                    if v.lower() == speaker.lower():
                        matched_speaker = v
                        break

                text_content = line.get("text", "").strip()
                if not text_content:
                    continue

                sound_tag = line.get("sound_tag") or ""
                sound_tag = sound_tag.lower().strip()
                if sound_tag not in KNOWN_TAGS:
                    sound_tag = ""

                delay_ms = int(line.get("delay_ms", 1600))
                delay_ms = max(800, min(3500, delay_ms))

                mood = line.get("mood", "neutral")

                validated_script.append({
                    "speaker": matched_speaker,
                    "text": text_content,
                    "sound_tag": sound_tag,
                    "delay_ms": delay_ms,
                    "mood": mood
                })

            return validated_script, fight
        except Exception as e:
            return [], {}

    def generate_single_reply(self, teammate: dict, user_message: str, game_context: dict, mood: dict) -> tuple[str, str, bool]:
        """Single line reply for direct player questions or mic commands."""
        if not self.google_api_key:
            return "", "", False

        start_time = time.time()
        self.record_request()
        self.logger.log(4, f"AI API called: {self.model_name} for direct player question")

        name = teammate.get("name", "Vikram")
        archetype = teammate.get("archetype", "Player")
        bio = teammate.get("bio", "")

        prompt = f"""You are {name} ({archetype}), playing Counter-Strike: Condition Zero with your friend.
Bio: {bio}
User says: "{user_message}"
Rules:
1. 2 to 12 words only. Real gamer slang.
2. Choose one optional sound tag from: {json.dumps(KNOWN_TAGS)}
3. Output strict JSON: {{"text": "...", "sound_tag": "..."}}
"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.google_api_key}"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.85, "maxOutputTokens": 100, "responseMimeType": "application/json"}
            }
            resp = requests.post(url, json=payload, timeout=2.5)
            duration_ms = int((time.time() - start_time) * 1000)
            if resp.status_code == 200:
                data = resp.json()
                raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                obj = json.loads(raw)
                text = obj.get("text", "").strip()
                tag = obj.get("sound_tag", "").lower().strip()
                if tag not in KNOWN_TAGS: tag = ""
                safe, _ = is_safe_line(text)
                if safe and text:
                    self.logger.log(5, f"AI answer received from {self.model_name} in {duration_ms}ms: '{text}' [Tag: {tag}]")
                    return text, tag, True
        except Exception:
            pass

        return "", "", False
