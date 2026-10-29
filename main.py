import sys
import os
import time
import socket
import argparse
import subprocess
import webbrowser
from brain.service import AIBrainService, is_hl_process_running
from ui.server import WebUIServer
from plugin.installer import setup_game_directory

def is_brain_already_running(host="127.0.0.1", port=27115) -> bool:
    """Return True if another AI Brain Service instance is already bound to UDP 27115."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((host, port))
        sock.close()
        return False
    except OSError:
        sock.close()
        return True

def main():
    parser = argparse.ArgumentParser(description="AI Teammates for Counter-Strike: Condition Zero")
    parser.add_argument("--no-ui", action="store_true", help="Run in headless console mode without Web UI")
    parser.add_argument("--port", type=int, default=5000, help="Web UI port (default 5000)")
    parser.add_argument("--setup", action="store_true", help="Auto-configure Condition Zero directories and exit")
    parser.add_argument("--launch-game", action="store_true", help="Launch hl.exe (Condition Zero) alongside the Brain")
    args = parser.parse_args()

    # Change working directory to project root so relative paths always work when launched from hl.exe
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    if args.setup:
        print("[Main] Running auto-configuration for Condition Zero...")
        setup_game_directory()
        return

    # Prevent duplicate instances when auto-launched by ai_launcher_amxx.dll on map load
    if is_brain_already_running():
        print("[Main] AI Brain Service is already running on UDP 127.0.0.1:27115.")
        return

    print("=" * 60)
    print("   AI Teammates for Counter-Strike: Condition Zero")
    print("   'Playing CZ with 4 friends who are always online'")
    print("=" * 60)

    # Ensure game directory and WAV sounds are installed in czero/
    setup_game_directory()

    # Initialize AI Brain Service (remains strictly idle until game connects, exits when game closes)
    brain = AIBrainService(exit_on_game_close=True)
    brain.start()

    # Optionally launch hl.exe if requested or via play_czero.bat
    if args.launch_game and not is_hl_process_running():
        hl_exe = os.path.join(project_root, "hl.exe")
        if os.path.exists(hl_exe):
            print("[Main] Launching Counter-Strike: Condition Zero (hl.exe)...")
            subprocess.Popen(
                [hl_exe, "-game", "czero", "-nomaster", "-insecure", "+exec", "listenserver.cfg"],
                cwd=project_root
            )
        else:
            print(f"[Main] ERROR: Could not find '{hl_exe}'. Please launch Condition Zero manually.")

    # Start Web Dashboard
    if not args.no_ui:
        ui = WebUIServer(brain, port=args.port)
        ui.start()
        dashboard_url = f"http://localhost:{ui.port}"
        print(f"\n[Main] Dashboard active at {dashboard_url}")
        if not args.launch_game:
            try:
                webbrowser.open(dashboard_url)
            except Exception:
                pass

    if is_hl_process_running():
        print("\n[Main] Condition Zero (hl.exe) detected! Waiting for in-game map heartbeat...")
    else:
        print("\n[Main] Brain is IDLE (no chat or sounds will play while game is closed).")
        print("       Launch Condition Zero (or run play_czero.bat) to activate teammates.")
    print("       Brain will automatically shut down within 5s when Condition Zero closes.")

    try:
        while brain.running and not brain.shutdown_requested:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[Main] Shutting down AI Teammates Service...")
    finally:
        brain.stop()
        print("[Main] Brain Service stopped cleanly. Goodbye!")

if __name__ == "__main__":
    main()
