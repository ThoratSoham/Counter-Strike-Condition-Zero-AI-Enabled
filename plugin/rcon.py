import socket
import struct
import time
import re

class GoldSrcRcon:
    """
    GoldSrc (Half-Life 1 / Condition Zero) UDP RCON protocol implementation.
    """
    def __init__(self, host="127.0.0.1", port=27015, password="czeroai", timeout=1.5):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(self.timeout)

    def _get_challenge(self):
        try:
            req = b'\xFF\xFF\xFF\xFFchallenge rcon\n'
            self.sock.sendto(req, (self.host, self.port))
            data, _ = self.sock.recvfrom(4096)
            # Response: \xFF\xFF\xFF\xFFchallenge rcon <number>\n
            match = re.search(r'challenge rcon (\d+)', data.decode('latin-1', errors='ignore'))
            if match:
                return match.group(1)
        except Exception:
            pass
        return ""

    def send_command(self, cmd: str) -> str:
        """Execute a console command via RCON."""
        challenge = self._get_challenge()
        if not challenge:
            # Fallback direct rcon format
            payload = f'\xFF\xFF\xFF\xFFrcon "{self.password}" {cmd}\n'.encode('latin-1')
        else:
            payload = f'\xFF\xFF\xFF\xFFrcon {challenge} "{self.password}" {cmd}\n'.encode('latin-1')

        try:
            self.sock.sendto(payload, (self.host, self.port))
            data, _ = self.sock.recvfrom(4096)
            # Response: \xFF\xFF\xFF\xFFl<response>
            text = data.decode('latin-1', errors='ignore')
            if text.startswith('\xFF\xFF\xFF\xFF'):
                text = text[4:]
            if text.startswith('l'):
                text = text[1:]
            return text.strip()
        except socket.timeout:
            return ""
        except Exception as e:
            return f"Error: {e}"

    def say_team(self, sender: str, message: str):
        """Send message into in-game team chat as the bot."""
        clean_msg = message.replace('"', "'").replace("\n", " ")
        return self.send_command(f'say_team "[{sender}] {clean_msg}"')

    def say_all(self, sender: str, message: str):
        """Send message into in-game all chat."""
        clean_msg = message.replace('"', "'").replace("\n", " ")
        return self.send_command(f'say "[{sender}] {clean_msg}"')

    def bot_order(self, order: str):
        """Send bot coordination order."""
        if order == "follow":
            self.send_command("bot_follow_user")
        elif order == "hold":
            self.send_command("bot_stop 1")
        elif order == "rush":
            self.send_command("bot_stop 0; bot_defer_to_human 0")
        elif order == "save":
            self.send_command("bot_defer_to_human 1")
