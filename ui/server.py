import http.server
import socketserver
import json
import urllib.parse
import os
import threading
from plugin.installer import setup_game_directory

class WebUIServer:
    def __init__(self, brain_service, port=5000):
        self.brain = brain_service
        self.port = port
        self.ui_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(self.ui_dir)
        self.log_file = os.path.join(self.base_dir, "logs", "mod.log")

    def start(self):
        handler = self._create_handler()
        try:
            self.httpd = socketserver.TCPServer(("", self.port), handler)
        except OSError:
            print(f"[WebUI] Port {self.port} in use, trying {self.port + 1}...")
            self.port += 1
            self.httpd = socketserver.TCPServer(("", self.port), handler)

        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        print(f"[WebUI] Command Center running at: http://localhost:{self.port}")

    def _create_handler(outer_self):
        class CustomHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                path = parsed.path
                query = urllib.parse.parse_qs(parsed.query)

                if path == "/" or path == "/index.html":
                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.end_headers()
                    with open(os.path.join(outer_self.ui_dir, "index.html"), "rb") as f:
                        self.wfile.write(f.read())
                    return

                if path == "/api/status":
                    self._send_json(outer_self._get_status())
                    return

                if path == "/api/diagnostics":
                    self._send_json(outer_self._run_diagnostics())
                    return

                if path == "/api/test_say":
                    outer_self.brain.respond_as_bot("vikram", "Hello! AI Teammate online and ready.", "hype")
                    self._send_json({"status": "ok", "message": "Triggered test say"})
                    return

                if path == "/api/test_ping":
                    outer_self.brain.logger.log(3, "Ping tested via Command Center.")
                    self._send_json({"status": "ok", "message": "PONG"})
                    return

                if path == "/api/test_sound":
                    tag = query.get("tag", ["hype"])[0]
                    label = outer_self.brain.meme_sound.play_tag(tag, is_critical=True)
                    self._send_json({"status": "ok", "tag": tag, "sound": label})
                    return

                if path == "/api/simulate_chat":
                    msg = query.get("msg", ["help"])[0]
                    outer_self.brain.handle_player_message(msg)
                    self._send_json({"status": "ok", "message": msg})
                    return

                self.send_error(404, "File not found")

            def do_POST(self):
                parsed = urllib.parse.urlparse(self.path)
                length = int(self.headers.get('content-length', 0))
                body = self.rfile.read(length).decode('utf-8') if length > 0 else ""

                if parsed.path == "/api/setup_game":
                    czero_path = os.path.join(outer_self.base_dir, "czero")
                    success = setup_game_directory(czero_path)
                    msg = "Condition Zero configured successfully with Metamod & AMX Mod X!" if success else "Setup error."
                    self._send_json({"status": "ok", "message": msg})
                    return

                if parsed.path == "/api/save_config":
                    try:
                        data = json.loads(body)
                        config_file = os.path.join(outer_self.base_dir, "config.json")
                        with open(config_file, "r", encoding="utf-8") as f:
                            cfg = json.load(f)
                        cfg.update(data)
                        with open(config_file, "w", encoding="utf-8") as f:
                            json.dump(cfg, f, indent=2)

                        # Apply live
                        outer_self.brain.llm_client.set_chat_style(cfg.get("chat_style", "full_gamer"))
                        outer_self.brain.llm_client.set_language(cfg.get("language", "en"))
                        if "gemini_api_key" in cfg:
                            outer_self.brain.llm_client.set_keys(cfg.get("gemini_api_key", ""), cfg.get("openrouter_api_key", ""))
                        if "sound_volume" in cfg:
                            outer_self.brain.meme_sound.volume = float(cfg["sound_volume"])
                        if "sound_frequency" in cfg:
                            outer_self.brain.meme_sound.frequency = cfg["sound_frequency"]

                        self._send_json({"status": "ok", "message": "Settings updated"})
                    except Exception as e:
                        self._send_json({"status": "error", "message": str(e)}, 500)
                    return

                self.send_error(404, "Unknown POST endpoint")

            def _send_json(self, data, code=200):
                self.send_response(code)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode('utf-8'))

        return CustomHandler

    def _get_status(self):
        tm_list = []
        for t_id in self.brain.teammates:
            pers = self.brain.voice_engine.get_personality(t_id)
            mood = self.brain.mood_manager.get_mood(t_id)
            tm_list.append({
                "id": t_id,
                "name": pers.get("name", t_id),
                "archetype": pers.get("archetype", ""),
                "tagline": pers.get("tagline", ""),
                "mood": mood
            })

        # Read last 20 log lines from logs/mod.log
        recent_logs = []
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    recent_logs = [l.strip() for l in lines[-25:] if l.strip()]
            except Exception:
                pass

        return {
            "teammates": tm_list,
            "energy": self.brain.budget_manager.get_stats(),
            "logs": recent_logs
        }

    def _run_diagnostics(self):
        api_prov = "Gemini Cloud" if self.brain.llm_client.gemini_api_key else "Offline (Local Reply Bank)"
        return {
            "plugin": True,
            "game_socket": True,
            "api_provider": api_prov
        }
