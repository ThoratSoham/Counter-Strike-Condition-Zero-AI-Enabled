"""
Multiplayer Host Launcher (MP01, MP06, MP10, MP12).
- Runs ONLY on the Host's PC.
- Configures local server rules & secret RCON password (never in Git).
- Detects Tailscale / ZeroTier VPN IP and displays the 'SHARE THIS' join line.
- Starts the AI Teammates Brain Service + Web Command Center on the Host.
- Launches Condition Zero Listen Server (`hl.exe`) or Dedicated Server (`hlds.exe`) for up to 24-32 players.
"""

import argparse
import os
import subprocess
import sys
import time
from brain.service import AIBrainService, is_hl_process_running
from multiplayer import DEFAULT_MAX_PLAYERS, DEFAULT_SERVER_PORT, MOD_VERSION
from multiplayer.installer_mp import (
    ensure_local_config,
    write_client_userconfig,
    write_multiplayer_secret_cfg,
    write_server_configs,
)
from multiplayer.vpn_check import detect_network_addresses
from plugin.installer import setup_game_directory
from ui.server import WebUIServer


def build_server_launch_cmd(
    base_dir: str,
    dedicated: bool = False,
    port: int = DEFAULT_SERVER_PORT,
    maxplayers: int = DEFAULT_MAX_PLAYERS,
    map_name: str = "de_dust2_cz",
) -> list[str]:
    max_p = max(2, min(32, int(maxplayers)))
    if dedicated:
        exe = os.path.join(base_dir, "hlds.exe")
        return [
            exe,
            "-console",
            "-game",
            "czero",
            "-nomaster",
            "-insecure",
            "+sv_lan",
            "1",
            "+port",
            str(port),
            "+maxplayers",
            str(max_p),
            "+exec",
            "server.cfg",
            "+map",
            map_name,
        ]
    else:
        exe = os.path.join(base_dir, "hl.exe")
        return [
            exe,
            "-game",
            "czero",
            "-nomaster",
            "-insecure",
            "+sv_lan",
            "1",
            "+port",
            str(port),
            "+maxplayers",
            str(max_p),
            "+exec",
            "listenserver.cfg",
            "+map",
            map_name,
        ]


def main(argv=None) -> int:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    czero_dir = os.path.join(base_dir, "czero")

    cfg = ensure_local_config(base_dir)

    parser = argparse.ArgumentParser(description="Host a Condition Zero Multiplayer Match with AI Teammates (MP01)")
    parser.add_argument("--dedicated", action="store_true", help="Launch dedicated server (hlds.exe) instead of listen server (hl.exe)")
    parser.add_argument("--map", default=cfg.get("mp_start_map", "de_dust2_cz"), help="Starting map (default: de_dust2_cz)")
    parser.add_argument("--maxplayers", type=int, default=int(cfg.get("mp_maxplayers", DEFAULT_MAX_PLAYERS)), help="Max player slots 2..32 (default: 24)")
    parser.add_argument("--bot-mode", choices=["off", "fill", "always"], default=cfg.get("mp_bot_mode", "fill"), help="AI bot slot mode: off | fill | always")
    parser.add_argument("--bots", type=int, default=int(cfg.get("mp_bot_count", 8)), help="Target AI bot count for fill/always modes (default: 8)")
    parser.add_argument("--match-name", default=cfg.get("match_name", "CZ AI Teammates Squad Lobby"), help="Scoreboard match banner name (MP12)")
    parser.add_argument("--port", type=int, default=int(cfg.get("server_port", DEFAULT_SERVER_PORT)), help="UDP server port (default: 27015)")
    parser.add_argument("--no-launch", action="store_true", help="Configure server and start AI Brain without launching hl.exe/hlds.exe (useful if opening hl.exe manually)")
    parser.add_argument("--dry-run", action="store_true", help="Print configuration and exit without starting services")
    args = parser.parse_args(argv)

    maxplayers = max(2, min(32, args.maxplayers))
    setup_game_directory(czero_dir)
    write_server_configs(czero_dir)
    write_client_userconfig(czero_dir, voice_key=cfg.get("ingame_voice_key", "k"))
    write_multiplayer_secret_cfg(
        czero_dir=czero_dir,
        rcon_password=cfg["rcon_password"],
        match_name=args.match_name,
        bot_mode=args.bot_mode,
        bot_count=args.bots,
        friendly_fire=cfg.get("mp_friendly_fire", 0),
    )

    net = detect_network_addresses()
    share_ip = net["preferred_ip"]

    print("=================================================================")
    print(f"  CZ AI TEAMMATES — MULTIPLAYER HOST ({MOD_VERSION})")
    print("=================================================================")
    print(f"  Match Name  : {args.match_name}")
    print(f"  Server Mode : {'Dedicated (hlds.exe)' if args.dedicated else 'Listen Server (hl.exe - Host & Play)'}")
    print(f"  Map & Slots : {args.map} | Max Players: {maxplayers} (Supports 10-32 friends)")
    print(f"  AI Bots     : Mode='{args.bot_mode.upper()}' | Target Bots={args.bots} (Host runs AI Brain)")
    print(f"  Voice Chat  : Enabled (Hold '{cfg.get('ingame_voice_key', 'k').upper()}' to talk to friends; Host 'V' for AI)")
    print("-----------------------------------------------------------------")
    if net["vpn_ip"]:
        print(f"  [OK] {net['vpn_provider']} VPN IP Detected : {net['vpn_ip']}")
    else:
        print("  [!] No Tailscale/ZeroTier VPN detected — showing LAN IP below.")
        print("      (For internet play with 10+ friends, open Tailscale or ZeroTier first!)")
    if net["lan_ip"]:
        print(f"  [i] Local LAN IP             : {net['lan_ip']}")
    print("=================================================================")
    print("  >>> SHARE THIS WITH YOUR FRIENDS <<<")
    print(f"      Option A (Easy)   : Double-click join.bat and enter:  {share_ip}")
    print(f"      Option B (Console): Open ~ console and type:          connect {share_ip}:{args.port}")
    print("=================================================================")
    print("  In-Game Host Commands: !match (Setup Menu) | !admin (Admin Menu) | !votemap | !ping")
    print("=================================================================")

    launch_cmd = build_server_launch_cmd(
        base_dir=base_dir,
        dedicated=args.dedicated,
        port=args.port,
        maxplayers=maxplayers,
        map_name=args.map,
    )

    if args.dry_run:
        print(f"  [Dry Run] Launch command: {' '.join(launch_cmd)}")
        return 0

    # Start AI Brain Service on Host
    brain = AIBrainService(exit_on_game_close=True)
    brain.start()

    webui = WebUIServer(brain, port=5000)
    webui.start()

    already_running = is_hl_process_running()
    if args.no_launch or already_running:
        if already_running:
            print("[Host] Condition Zero (hl.exe / hlds.exe) is already running!")
            print(f"[Host] In the game console (~), run:  maxplayers {maxplayers}; sv_lan 0; map {args.map}")
        else:
            print("[Host] --no-launch active. Open hl.exe -> Change Game -> Condition Zero, or start a New Multiplayer Game.")
    else:
        exe_path = launch_cmd[0]
        if os.path.exists(exe_path):
            print(f"[Host] Launching server: {' '.join(os.path.basename(x) if i == 0 else x for i, x in enumerate(launch_cmd))}")
            subprocess.Popen(launch_cmd, cwd=base_dir)
        else:
            print(f"[Host] Warning: Could not find {exe_path}. Start Condition Zero manually.")

    try:
        while brain.running and not brain.shutdown_requested:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[Host] Stopping AI Brain and shutting down host helper...")
        brain.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())

