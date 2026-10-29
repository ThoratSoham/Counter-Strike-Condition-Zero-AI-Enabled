import socket
import threading
import re
import time
from brain.logger import get_logger

BOT_NAMES = ["vikram", "kabir", "marcus", "sunny"]

class GameBridge:
    """
    Listens for AMX Mod X native plugin UDP packets (including 2s HEARTBEAT)
    and standard GoldSrc logs.
    Tracks live connection state so the Brain NEVER runs chat or sounds when disconnected.
    """
    RE_KILL = re.compile(r'^"(.+?)<\d+><[^>]*><(CT|TERRORIST)>" killed "(.+?)<\d+><[^>]*><(CT|TERRORIST)>" with "([^"]+)"(?:\s*\((headshot)\))?')
    RE_ROUND_START = re.compile(r'World triggered "Round_Start"')
    RE_ROUND_END = re.compile(r'World triggered "Round_End"')
    RE_BOMB_PLANTED = re.compile(r'^"(.+?)<\d+><[^>]*><TERRORIST>" triggered "Planted_The_Bomb"')
    RE_BOMB_DEFUSED = re.compile(r'^"(.+?)<\d+><[^>]*><CT>" triggered "Defused_The_Bomb"')
    RE_TARGET_BOMBED = re.compile(r'Target_Bombed')
    RE_CHAT = re.compile(r'^"(.+?)<\d+><[^>]*><(CT|TERRORIST)>" say(_team)? "(.+?)"')

    def __init__(self, host="127.0.0.1", port=27115, event_handler=None):
        self.host = host
        self.port = port
        self.event_handler = event_handler
        self.running = False
        self.sock = None
        self.plugin_addr = None
        self.is_connected = False
        self.last_heartbeat = 0.0
        self.logger = get_logger()

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        self.logger.log(0, f"GameBridge UDP listener active on {self.host}:{self.port}")

    def stop(self):
        self.running = False
        self.is_connected = False
        self.plugin_addr = None
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass

    def mark_disconnected(self):
        self.is_connected = False
        self.plugin_addr = None

    def send_to_plugin(self, message: str):
        """Send command packet back to the connected AMX Mod X plugin."""
        if self.sock and self.plugin_addr and self.is_connected:
            try:
                payload = message.encode('latin-1', errors='replace')
                self.sock.sendto(payload, self.plugin_addr)
                return True
            except Exception as e:
                print(f"[GameBridge] Failed to send to plugin {self.plugin_addr}: {e}")
        return False

    def _record_heartbeat(self, addr):
        was_connected = self.is_connected
        self.plugin_addr = addr
        self.last_heartbeat = time.time()
        self.is_connected = True
        return not was_connected

    def _notify_if_newly_connected(self, newly_connected: bool, addr):
        if newly_connected and self.event_handler:
            self.event_handler("game_connected", {"addr": f"{addr[0]}:{addr[1]}"})

    def _listen_loop(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.bind((self.host, self.port))
        except Exception as e:
            self.logger.log_offline(f"Could not bind UDP {self.host}:{self.port}: {e}")
            self.running = False
            return

        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                if not data:
                    continue
                text = data.decode('latin-1', errors='ignore').strip()

                # 1. AMX Mod X Native Protocol
                if (
                    text.startswith("HEARTBEAT")
                    or text.startswith("PING")
                    or text.startswith("GOODBYE")
                    or text.startswith("EVENT|")
                    or text.startswith("TEST_SOUND|")
                    or text in ["FORCE_FIGHT", "FORCE_CHAT", "RESET", "GET_STATUS", "SOUND_LIST"]
                ):
                    self._parse_amx_packet(text, addr)
                    continue

                # 2. Standard GoldSrc Engine Logs
                if text.startswith('\xFF\xFF\xFF\xFF'):
                    text = text[4:]
                if text.startswith('l'):
                    text = text[1:]

                for line in text.split('\n'):
                    line = line.strip()
                    if line:
                        self._parse_goldsrc_line(line)
            except Exception as e:
                if self.running:
                    print(f"[GameBridge] Socket read error: {e}")

    def _parse_amx_packet(self, text: str, addr):
        parts = text.split("|")
        cmd = parts[0]

        if cmd == "GOODBYE":
            self.logger.log(0, "Brain service received GOODBYE (game/map closing) from AMX Mod X plugin.")
            self.mark_disconnected()
            if self.event_handler:
                self.event_handler("game_disconnected", {"reason": "plugin_goodbye"})
            return

        # Any valid packet from the plugin counts as a live heartbeat
        newly_connected = self._record_heartbeat(addr)
        self._notify_if_newly_connected(newly_connected, addr)

        if cmd == "HEARTBEAT":
            self.send_to_plugin("HEARTBEAT_ACK")
            return

        if cmd == "PING":
            self.logger.log(3, "Brain service received PING from AMX Mod X plugin.")
            self.send_to_plugin("PONG")
            return

        if cmd == "FORCE_FIGHT":
            if self.event_handler:
                self.event_handler("force_fight", {})
            return

        if cmd == "FORCE_CHAT":
            if self.event_handler:
                self.event_handler("force_chat", {})
            return

        if cmd == "RESET":
            if self.event_handler:
                self.event_handler("reset", {})
            return

        if cmd == "TEST_SOUND":
            tag = parts[1] if len(parts) > 1 else "hype"
            requester = parts[2] if len(parts) > 2 else ""
            reason = parts[3] if len(parts) > 3 else f"command ai_test_sound {tag}"
            if self.event_handler:
                self.event_handler("test_sound", {"tag": tag, "requester": requester, "reason": reason})
            return

        if cmd == "EVENT":
            evt_type = parts[1] if len(parts) > 1 else ""
            if evt_type == "chat":
                sender = parts[2] if len(parts) > 2 else "Player"
                team = parts[3] if len(parts) > 3 else "CT"
                is_team = parts[4] == "1" if len(parts) > 4 else True
                msg = parts[5] if len(parts) > 5 else ""

                if any(b in sender.lower() for b in BOT_NAMES) or msg.startswith("[") or msg.startswith("*plays "):
                    return

                self.logger.log(3, f"Brain service received event: player_chat by '{sender}' ('{msg}')")
                if self.event_handler:
                    self.event_handler("chat", {
                        "sender": sender,
                        "team": team,
                        "is_team": is_team,
                        "message": msg
                    })
            elif evt_type == "kill":
                killer = parts[2] if len(parts) > 2 else ""
                victim = parts[3] if len(parts) > 3 else ""
                weapon = parts[4] if len(parts) > 4 else ""
                headshot = parts[5] == "1" if len(parts) > 5 else False

                self.logger.log(3, f"Brain service received event: kill by '{killer}' on '{victim}' with '{weapon}' (hs:{headshot})")
                if self.event_handler:
                    self.event_handler("kill", {
                        "attacker": killer,
                        "victim": victim,
                        "weapon": weapon,
                        "headshot": headshot
                    })
            elif evt_type == "round_end":
                won = parts[2] == "1" if len(parts) > 2 else True
                self.logger.log(3, f"Brain service received event: round_end (won: {won})")
                if self.event_handler:
                    self.event_handler("round_end", {"won": won})
            elif evt_type in ["round_start", "bomb_planted", "bomb_defused", "bomb_exploded"]:
                self.logger.log(3, f"Brain service received event: {evt_type}")
                if self.event_handler:
                    self.event_handler(evt_type, {})

    def _parse_goldsrc_line(self, line: str):
        if line.startswith('L '):
            parts = line.split(': ', 1)
            if len(parts) == 2:
                line = parts[1]

        m = self.RE_KILL.search(line)
        if m:
            atk, atk_team, vic, vic_team, wpn, hs = m.groups()
            self._dispatch("kill", {"attacker": atk, "victim": vic, "weapon": wpn, "headshot": bool(hs)})
            return

        if self.RE_ROUND_START.search(line):
            self._dispatch("round_start", {})
            return

        m = self.RE_BOMB_PLANTED.search(line)
        if m:
            self._dispatch("bomb_planted", {"planter": m.group(1)})
            return

        m = self.RE_CHAT.search(line)
        if m:
            sender, team, is_team, msg = m.groups()
            if any(b in sender.lower() for b in BOT_NAMES) or msg.startswith("[") or msg.startswith('"['):
                return
            self._dispatch("chat", {"sender": sender, "team": team, "is_team": bool(is_team), "message": msg})
            return

    def _dispatch(self, event_name, data):
        if not self.is_connected:
            return
        self.logger.log(3, f"Brain service received log event: {event_name}")
        if self.event_handler:
            self.event_handler(event_name, data)
