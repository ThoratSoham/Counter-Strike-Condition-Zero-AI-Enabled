"""
Multiplayer Friend Join Helper (MP02, MP03, MP11, MP14, MP15).
- Runs on Joining Friends' PCs.
- NEVER starts the AI Brain (the Host runs the AI Brain for everyone).
- Remembers the last Host VPN IP in `.last_host.txt`.
- Configures client `userconfig.cfg` (mod version tag, VPN rates, built-in voice key).
- Checks VPN ping & server status via A2S_INFO before launching Condition Zero + connecting.
"""

import argparse
import os
import subprocess
import sys
from multiplayer import DEFAULT_SERVER_PORT, MOD_VERSION
from multiplayer.installer_mp import write_client_userconfig
from multiplayer.vpn_check import (
    detect_network_addresses,
    parse_host_port,
    ping_host_icmp,
    query_goldsrc_server,
)


def load_last_host(base_dir: str) -> str:
    last_file = os.path.join(base_dir, ".last_host.txt")
    if os.path.exists(last_file):
        try:
            with open(last_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return ""


def save_last_host(base_dir: str, host_str: str):
    last_file = os.path.join(base_dir, ".last_host.txt")
    try:
        with open(last_file, "w", encoding="utf-8") as f:
            f.write(host_str.strip() + "\n")
    except Exception:
        pass


def build_join_launch_cmd(base_dir: str, host: str, port: int = DEFAULT_SERVER_PORT, player_name: str = "") -> list[str]:
    exe = os.path.join(base_dir, "hl.exe")
    cmd = [
        exe,
        "-game",
        "czero",
        "-nomaster",
        "-insecure",
        "+exec",
        "userconfig.cfg",
    ]
    if player_name.strip():
        cmd.extend(["+name", player_name.strip()])
    cmd.extend(["+connect", f"{host}:{port}"])
    return cmd


def main(argv=None) -> int:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    czero_dir = os.path.join(base_dir, "czero")

    parser = argparse.ArgumentParser(description="Join a Friend's Condition Zero AI Teammates Match (MP02)")
    parser.add_argument("--host", default="", help="Host VPN/LAN IP (e.g., 100.84.12.5 or 100.84.12.5:27015)")
    parser.add_argument("--name", default="", help="Optional in-game player nickname")
    parser.add_argument("--voice-key", default="k", help="In-game push-to-talk key for voice chat (default: k)")
    parser.add_argument("--dry-run", action="store_true", help="Test ping and print launch command without opening hl.exe")
    args = parser.parse_args(argv)

    print("=================================================================")
    print(f"  CZ AI TEAMMATES — JOIN FRIEND'S MATCH ({MOD_VERSION})")
    print("  (Client Mode: AI Brain runs on Host PC — no API key needed!)")
    print("=================================================================")

    net = detect_network_addresses()
    if net["vpn_ip"]:
        print(f"  [OK] Your {net['vpn_provider']} IP : {net['vpn_ip']}")
    else:
        print("  [!] Note: Tailscale / ZeroTier VPN was not detected.")
        print("      (If joining over the internet, connect to your friend's VPN first.)")

    # Configure client userconfig.cfg (MP03 version tag, MP11 voice bind, MP14 VPN rates)
    if os.path.exists(czero_dir):
        write_client_userconfig(czero_dir, voice_key=args.voice_key)
        print(f"  [OK] Configured client voice (Hold '{args.voice_key.upper()}' to talk) & VPN rates.")

    remembered = load_last_host(base_dir)
    target = args.host.strip()
    if not target and not args.dry_run:
        prompt = f"\n  Enter Host VPN IP [{remembered}]: " if remembered else "\n  Enter Host VPN IP (from friend's host.bat): "
        try:
            entered = input(prompt).strip()
        except EOFError:
            entered = ""
        target = entered or remembered
    elif not target:
        target = remembered or "127.0.0.1"

    if not target:
        print("  [Error] No Host IP entered. Run join.bat again once your friend shares their IP.")
        return 1

    host, port = parse_host_port(target)
    save_last_host(base_dir, f"{host}:{port}" if port != DEFAULT_SERVER_PORT else host)

    print(f"\n  Checking connection to {host}:{port} ...")
    icmp_ms = ping_host_icmp(host)
    if icmp_ms is not None:
        print(f"  [OK] VPN Ping       : {icmp_ms:.0f} ms")

    srv = query_goldsrc_server(host, port=port, timeout=2.0)
    if srv["online"] and srv["info"]:
        info = srv["info"]
        print(f"  [OK] Match Found    : {info['name']}")
        print(f"       Map & Players  : {info['map']} ({info['players']}/{info['max_players']} slots, RTT {srv['ping_ms']} ms)")
    else:
        print(f"  [!] Server query did not reply yet ({srv['error']}).")
        print("      Launching anyway — Condition Zero will retry connecting automatically.")

    launch_cmd = build_join_launch_cmd(base_dir, host, port=port, player_name=args.name)
    print("-----------------------------------------------------------------")
    print(f"  Console Join Backup : connect {host}:{port}")
    print("  In-Game Commands    : !ping | !mictest | !sounds | !votemap | /spec")
    print("=================================================================")

    if args.dry_run:
        print(f"  [Dry Run] Client command: {' '.join(launch_cmd)}")
        return 0

    exe_path = launch_cmd[0]
    if not os.path.exists(exe_path):
        print(f"  [Error] Could not find {exe_path}. Place join.bat in your Condition Zero folder.")
        return 1

    print("  Launching Counter-Strike: Condition Zero and connecting to match...")
    subprocess.Popen(launch_cmd, cwd=base_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())

