"""
Comprehensive Automated Verification Suite for Section 19 Multiplayer Mod (MP01 - MP15).
Verifies:
  1. MP01 / MP02 / MP2: `install.bat`, `host.bat`, `join.bat`, host & join command builders, `.last_host.txt` persistence, and client mode never starting AI Brain.
  2. MP03 / MP11 / MP14: `czero/userconfig.cfg` (`ai_mod_ver "2.0.0-MP"`, `bind "k" "+voicerecord"`, VPN rates) and `czero/vpn_net.cfg`.
  3. MP10: Zero hardcoded `rcon_password` in tracked repo `.cfg`/`.py`/`.json` files; secret stored only in gitignored `czero/multiplayer_secret.cfg` & `config.json`.
  4. MP15: Tailscale / ZeroTier / LAN IP detection + live UDP `A2S_INFO` server query & RTT measurement (including `0x41` challenge handshake).
  5. MP04 / MP06 / MP07 / 19.4: Live `AIBrainService` multiplayer UDP protocol (`ROSTER|10|...`, `SET_STYLE|clean`, `EVENT|kill|...|killer_human|victim_human`, multi-friend chat replies, 15-line batch scaling for 10+ friends, and wider idle gap when 6+ humans or low budget).
  6. MP03-MP15 Pawn Plugin Audit: Compiled `czero_ai_teammates.amxx` exists and `czero_ai_teammates.sma` implements all required multiplayer menus, commands, reconnect restore, map vote, and silent `spk` sound fallback (no `precache_sound`).
"""

import os
import socket
import subprocess
import sys
import threading
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from brain.service import AIBrainService
from multiplayer import MOD_VERSION
from multiplayer.host_manager import build_server_launch_cmd
from multiplayer.installer_mp import install_multiplayer
from multiplayer.join_helper import build_join_launch_cmd, load_last_host, save_last_host
from multiplayer.vpn_check import (
    detect_network_addresses,
    parse_a2s_info_response,
    parse_host_port,
    query_goldsrc_server,
)


def test_1_launchers_and_configs():
    print("\n[MP TEST 1] Verifying install.bat, host.bat, join.bat, VPN tuning & client voice config (MP01, MP02, MP03, MP11, MP14)...")
    for script in ("install.bat", "host.bat", "join.bat", "check_vpn.py", "docs/MULTIPLAYER.md"):
        full = os.path.join(BASE_DIR, script)
        assert os.path.exists(full), f"Missing required multiplayer file: {script}"

    cfg = install_multiplayer(BASE_DIR)
    assert cfg.get("rcon_password") and cfg["rcon_password"] != "czeroai", "MP10: RCON password must be uniquely generated"

    # Verify host launch commands (Listen & Dedicated 24-slot)
    listen_cmd = build_server_launch_cmd(BASE_DIR, dedicated=False, port=27015, maxplayers=24, map_name="de_dust2_cz")
    assert os.path.basename(listen_cmd[0]).lower() == "hl.exe"
    assert "+maxplayers" in listen_cmd and "24" in listen_cmd
    assert "-steam" not in listen_cmd, "Standalone build must not pass -steam"

    ded_cmd = build_server_launch_cmd(BASE_DIR, dedicated=True, port=27015, maxplayers=28, map_name="de_inferno_cz")
    assert os.path.basename(ded_cmd[0]).lower() == "hlds.exe"
    assert "28" in ded_cmd and "server.cfg" in ded_cmd

    # Verify join launch command & last host persistence (MP02)
    save_last_host(BASE_DIR, "100.84.12.5")
    assert load_last_host(BASE_DIR) == "100.84.12.5"
    join_cmd = build_join_launch_cmd(BASE_DIR, "100.84.12.5", port=27015, player_name="Soham")
    assert "+connect" in join_cmd and "100.84.12.5:27015" in join_cmd

    # Clean up test .last_host.txt
    last_file = os.path.join(BASE_DIR, ".last_host.txt")
    if os.path.exists(last_file):
        os.remove(last_file)

    # Verify userconfig.cfg (MP03, MP11, MP14) & vpn_net.cfg (MP14)
    with open(os.path.join(BASE_DIR, "czero", "userconfig.cfg"), "r", encoding="latin-1") as f:
        ucfg = f.read()
    assert f'setinfo "ai_mod_ver" "{MOD_VERSION}"' in ucfg, "MP03 version setinfo missing in userconfig.cfg"
    assert 'bind "k" "+voicerecord"' in ucfg.lower(), "MP11 voice bind missing in userconfig.cfg"
    assert 'rate "25000"' in ucfg, "MP14 rate missing in userconfig.cfg"

    with open(os.path.join(BASE_DIR, "czero", "vpn_net.cfg"), "r", encoding="latin-1") as f:
        vcfg = f.read()
    assert "sv_lan 1" in vcfg and "sv_lan 0" not in vcfg, "Protocol 47 standalone build requires sv_lan 1 so New Game never hangs on Speakeasy.net VAC auth"
    assert "sv_maxrate 25000" in vcfg and "sv_lan_rate 25000" in vcfg and "sv_unlag 1" in vcfg, "MP14 VPN server tuning missing"

    # Dry-run CLI check for host_manager and join_helper
    r_host = subprocess.run([sys.executable, "-m", "multiplayer.host_manager", "--dry-run", "--maxplayers", "24"], cwd=BASE_DIR, capture_output=True, text=True, timeout=10)
    assert r_host.returncode == 0 and "SHARE THIS WITH YOUR FRIENDS" in r_host.stdout

    r_join = subprocess.run([sys.executable, "-m", "multiplayer.join_helper", "--host", "127.0.0.1:27015", "--dry-run"], cwd=BASE_DIR, capture_output=True, text=True, timeout=10)
    assert r_join.returncode == 0 and "Client Mode: AI Brain runs on Host PC" in r_join.stdout

    print("  [OK] MP TEST 1 PASSED.")


def test_2_mp10_secret_isolation():
    print("\n[MP TEST 2] Verifying RCON password & secrets are NEVER hardcoded in tracked files (MP10)...")
    tracked_files_to_check = [
        os.path.join(BASE_DIR, "czero", "listenserver.cfg"),
        os.path.join(BASE_DIR, "czero", "server.cfg"),
        os.path.join(BASE_DIR, "plugin", "installer.py"),
        os.path.join(BASE_DIR, "config.example.json"),
    ]
    for path in tracked_files_to_check:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        assert 'rcon_password "czeroai"' not in content, f"MP10 violation: hardcoded rcon_password found in {path}"
        if path.endswith(".cfg"):
            assert "rcon_password" not in content, f"MP10 violation: rcon_password line found in tracked {path}"
            assert "exec multiplayer_secret.cfg" in content, f"{path} must exec multiplayer_secret.cfg"

    with open(os.path.join(BASE_DIR, ".gitignore"), "r", encoding="utf-8") as f:
        gi = f.read()
    assert "multiplayer_secret.cfg" in gi and "config.json" in gi
    assert os.path.exists(os.path.join(BASE_DIR, "czero", "multiplayer_secret.cfg"))
    print("  [OK] MP TEST 2 PASSED.")


def test_3_vpn_detection_and_a2s_ping():
    print("\n[MP TEST 3] Verifying VPN adapter detection & UDP A2S_INFO server query / RTT ping (MP15)...")
    sample_ipconfig = """
Windows IP Configuration

Unknown adapter Tailscale:

   Connection-specific DNS Suffix  . : tail1234.ts.net
   Description . . . . . . . . . . . : Tailscale Tunnel
   IPv4 Address. . . . . . . . . . . : 100.92.44.18(Preferred)

Ethernet adapter Ethernet:

   Description . . . . . . . . . . . : Realtek PCIe GbE Family Controller
   IPv4 Address. . . . . . . . . . . : 192.168.1.50(Preferred)
"""
    detected = detect_network_addresses(ipconfig_override=sample_ipconfig)
    assert detected["vpn_provider"] == "Tailscale"
    assert detected["vpn_ip"] == "100.92.44.18"
    assert detected["lan_ip"] == "192.168.1.50"
    assert detected["preferred_ip"] == "100.92.44.18"
    assert parse_host_port("connect 100.92.44.18:27016") == ("100.92.44.18", 27016)

    # Spin up a mock GoldSrc UDP server implementing 0x41 challenge + 0x49 A2S_INFO reply
    srv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    srv_sock.bind(("127.0.0.1", 0))
    mock_port = srv_sock.getsockname()[1]

    def _mock_goldsrc_a2s():
        srv_sock.settimeout(3.0)
        try:
            pkt1, client_addr = srv_sock.recvfrom(1024)
            if pkt1.startswith(b"\xFF\xFF\xFF\xFFTSource Engine Query\x00"):
                # Send challenge 0x41
                srv_sock.sendto(b"\xFF\xFF\xFF\xFF\x41\x11\x22\x33\x44", client_addr)
                pkt2, client_addr = srv_sock.recvfrom(1024)
                assert pkt2.endswith(b"\x11\x22\x33\x44")
                payload = (
                    b"\xFF\xFF\xFF\xFF\x49\x30"
                    b"CZ AI Squad Lobby\x00"
                    b"de_dust2_cz\x00"
                    b"czero\x00"
                    b"Condition Zero\x00"
                    b"\x50\x00"  # appid 80
                    b"\x0E\x18\x04"  # 14 players, 24 max, 4 bots
                    b"dw\x00\x00"
                )
                srv_sock.sendto(payload, client_addr)
        finally:
            srv_sock.close()

    t = threading.Thread(target=_mock_goldsrc_a2s, daemon=True)
    t.start()

    res = query_goldsrc_server("127.0.0.1", port=mock_port, timeout=2.0)
    t.join(timeout=2.0)

    assert res["online"] is True, f"A2S query failed: {res}"
    assert res["ping_ms"] is not None and res["ping_ms"] >= 0.0
    assert res["info"]["name"] == "CZ AI Squad Lobby"
    assert res["info"]["map"] == "de_dust2_cz"
    assert res["info"]["players"] == 14
    assert res["info"]["max_players"] == 24
    assert res["info"]["bots"] == 4

    # Also test legacy GoldSrc 'm' (0x6D) packet format
    legacy_pkt = (
        b"\xFF\xFF\xFF\xFF\x6D"
        b"127.0.0.1:27015\x00"
        b"Legacy CZ Host\x00"
        b"de_inferno_cz\x00"
        b"czero\x00"
        b"Condition Zero\x00"
        b"\x0A\x14\x2F"
    )
    legacy_info = parse_a2s_info_response(legacy_pkt)
    assert legacy_info and legacy_info["players"] == 10 and legacy_info["max_players"] == 20
    print("  [OK] MP TEST 3 PASSED.")


def test_4_multi_human_brain_reactions_and_scaling():
    print("\n[MP TEST 4] Verifying 10-friend ROSTER scaling, SET_STYLE, and multi-human kill/death/chat reactions (MP04, MP07, 19.4)...")
    test_port = 27229
    cfg_override_path = os.path.join(BASE_DIR, "logs", "_test_mp_config.json")
    os.makedirs(os.path.dirname(cfg_override_path), exist_ok=True)
    with open(cfg_override_path, "w", encoding="utf-8") as f:
        f.write(f'{{"log_listener_port": {test_port}, "sounds_enabled": true, "google_api_key": ""}}')

    brain = AIBrainService(config_path=cfg_override_path, exit_on_game_close=False)
    # Disable mic listener during automated test
    brain.stt_listener.start_listening = lambda: None
    brain.stt_listener.stop_listening = lambda: None
    brain.start()

    plugin_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    plugin_sock.settimeout(3.0)
    received = []
    stop_rx = threading.Event()

    def _rx_loop():
        while not stop_rx.is_set():
            try:
                data, _ = plugin_sock.recvfrom(4096)
                received.append(data.decode("latin-1", errors="ignore"))
            except socket.timeout:
                continue
            except Exception:
                break

    rx_thread = threading.Thread(target=_rx_loop, daemon=True)
    rx_thread.start()

    try:
        # 1. Connect via HEARTBEAT
        plugin_sock.sendto(b"HEARTBEAT|alive", ("127.0.0.1", test_port))
        time.sleep(0.3)
        assert brain.is_game_connected()

        # 2. Send 10-human ROSTER packet (Section 19.1: 10+ friends)
        ten_friends = "Soham,Rahul,Aarav,Rohan,Priya,Neha,Karan,Dev,Ananya,Arjun"
        plugin_sock.sendto(f"ROSTER|10|{ten_friends}|de_dust2_cz".encode("latin-1"), ("127.0.0.1", test_port))
        time.sleep(0.3)
        assert len(brain.connected_humans) == 10
        assert brain.chatter_engine.get_target_batch_size() == 15, "Batch size must scale to 15 for 4+ humans"
        gap = brain.chatter_engine._sample_gap()
        assert 22.0 <= gap <= 38.0, f"Idle gap must widen to 22-38s for 6+ humans, got {gap}"

        # 3. Test SET_STYLE from Match Setup Menu (MP04)
        plugin_sock.sendto(b"SET_STYLE|clean", ("127.0.0.1", test_port))
        time.sleep(0.3)
        assert brain.chat_style == "clean" and brain.chatter_engine.chat_style == "clean"

        # 4. Test friend chat reply addressing that specific friend (MP07)
        received.clear()
        plugin_sock.sendto(b"EVENT|chat|Rahul|TERRORIST|1|guys cover me on B!", ("127.0.0.1", test_port))
        deadline = time.time() + 3.0
        while time.time() < deadline and not any(p.startswith("SAY|") for p in received):
            time.sleep(0.1)
        say_pkts = [p for p in received if p.startswith("SAY|")]
        assert say_pkts, f"Expected bot reply to Rahul, got {received}"
        assert "rahul" in say_pkts[0].lower(), f"Expected reply to address Rahul: {say_pkts[0]}"

        # 5. Test friend headshot kill hype reaction (MP07)
        received.clear()
        brain.last_kill_react_time = 0.0
        plugin_sock.sendto(b"EVENT|kill|Priya|Opie|ak47|1|1|0", ("127.0.0.1", test_port))
        deadline = time.time() + 3.0
        while time.time() < deadline and not any(p.startswith("SAY|") for p in received):
            time.sleep(0.1)
        say_kill = [p for p in received if p.startswith("SAY|")]
        assert say_kill and "priya" in say_kill[0].lower(), f"Expected bot hype mentioning Priya: {received}"

        # 6. Test friend death roast reaction (MP07)
        received.clear()
        brain.last_kill_react_time = 0.0
        plugin_sock.sendto(b"EVENT|kill|Frank|Arjun|awp|0|0|1", ("127.0.0.1", test_port))
        deadline = time.time() + 3.0
        while time.time() < deadline and not any(p.startswith("SAY|") for p in received):
            time.sleep(0.1)
        say_death = [p for p in received if p.startswith("SAY|")]
        assert say_death and "arjun" in say_death[0].lower(), f"Expected bot roast mentioning Arjun: {received}"

    finally:
        stop_rx.set()
        plugin_sock.close()
        brain.stop()
        if os.path.exists(cfg_override_path):
            os.remove(cfg_override_path)

    print("  [OK] MP TEST 4 PASSED.")


def test_5_pawn_plugin_audit():
    print("\n[MP TEST 5] Auditing compiled czero_ai_teammates.amxx & Pawn source for MP03-MP15 & silent sound safety...")
    sma_path = os.path.join(BASE_DIR, "czero", "addons", "amxmodx", "scripting", "czero_ai_teammates.sma")
    amxx_path = os.path.join(BASE_DIR, "czero", "addons", "amxmodx", "plugins", "czero_ai_teammates.amxx")
    assert os.path.exists(amxx_path) and os.path.getsize(amxx_path) > 20000

    with open(sma_path, "r", encoding="utf-8") as f:
        sma = f.read()

    required_markers = [
        '#define PLUGIN_VERSION "2.0.0-MP"',
        "client_putinserver",             # MP03 / MP12 / MP13
        'get_user_info(id, "ai_mod_ver"', # MP03 version check
        "cmd_ai_match_menu",              # MP04 match setup menu
        "cmd_ai_balance",                 # MP05 10+ player team balance
        "move_player_to_spec",            # MP05 spectators
        "sync_multiplayer_task",          # MP06 bot filling & human slot priority
        "cmd_ai_admin_menu",              # MP08 admin menu
        "cmd_ai_kick",                    # MP08 kick
        "cmd_ai_ban",                     # MP08 ban
        "cmd_ai_pause",                   # MP08 pause
        "cmd_ai_votemap",                 # MP09 map vote
        "cmd_ai_voice_test",              # MP11 mic loopback test
        "find_reconnect_team",            # MP13 reconnect team restore
        "cmd_ai_ping",                    # MP15 live VPN ping
        'register_cvar("ai_chat_bg"',     # Low-opacity black chat background cvar
        "push_chat_bg_line",              # Rolling 3-line VGUI2 black backdrop feed
        'get_user_msgid("TutorText")',    # Condition Zero native VGUI2 panel message
        "cmd_ai_chat_bg_toggle",          # !chatbg / ai_chat_bg_toggle command
    ]
    for marker in required_markers:
        assert marker in sma, f"Missing required multiplayer symbol in .sma: {marker}"

    # Verify Low-Opacity Black Chat Background VGUI2 resource files & silent tutor WAV
    tutor_scheme = os.path.join(BASE_DIR, "czero", "resource", "TutorScheme.res")
    tutor_win = os.path.join(BASE_DIR, "czero", "resource", "UI", "TutorTextWindow.res")
    client_scheme = os.path.join(BASE_DIR, "czero", "resource", "ClientScheme.res")
    silent_tutor_wav = os.path.join(BASE_DIR, "czero", "sound", "events", "tutor_msg.wav")
    for p in (tutor_scheme, tutor_win, client_scheme, silent_tutor_wav):
        assert os.path.exists(p), f"Missing chat backdrop asset: {p}"

    with open(tutor_scheme, "r", encoding="latin-1") as f:
        ts_txt = f.read()
    assert '"0 0 0 115"' in ts_txt, "TutorScheme.res must set low-opacity black WindowBG (0 0 0 115)"

    with open(client_scheme, "r", encoding="latin-1") as f:
        cs_txt = f.read()
    assert '"0 0 0 115"' in cs_txt and '"EngineFont"' in cs_txt and '"dropshadow"' in cs_txt

    # Section 19.4 critical safety rule: NEVER call precache_sound, which forces missing-file disconnects
    assert "precache_sound" not in sma, "19.4 violation: precache_sound must NOT be used so clients missing sounds never disconnect!"
    assert "#include <cstrike>" not in sma, "Must not depend on <cstrike> gamedata on Condition Zero mp.dll"
    print("  [OK] MP TEST 5 PASSED.")


def main():
    print("=================================================================")
    print("   RUNNING SECTION 19 MULTIPLAYER VERIFICATION SUITE (MP01-MP15)")
    print("=================================================================")
    test_1_launchers_and_configs()
    test_2_mp10_secret_isolation()
    test_3_vpn_detection_and_a2s_ping()
    test_4_multi_human_brain_reactions_and_scaling()
    test_5_pawn_plugin_audit()
    print("\n=================================================================")
    print("   ALL SECTION 19 MULTIPLAYER TESTS PASSED SUCCESSFULLY!")
    print("=================================================================")


if __name__ == "__main__":
    main()

