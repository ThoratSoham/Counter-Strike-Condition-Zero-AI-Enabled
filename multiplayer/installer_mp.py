"""
One-Click Multiplayer & Single-Player Setup Installer (MP2, MP03, MP10, MP11, MP14).
Configures:
  1. Metamod + AMX Mod X + czero_ai_teammates.amxx
  2. Local-only RCON secret in gitignored `czero/multiplayer_secret.cfg` (MP10)
  3. VPN-tuned GoldSrc network config `czero/vpn_net.cfg` (MP14)
  4. Client voice, network rates, and version tag `czero/userconfig.cfg` (MP03, MP11, MP14)
  5. Listen & Dedicated server configs (`czero/listenserver.cfg`, `czero/server.cfg`)
  6. Verified 16-bit 22050 Hz mono GoldSrc WAV sound bank
"""

import json
import os
import re
import secrets
import shutil
import string
import sys
import wave
from multiplayer import DEFAULT_MAX_PLAYERS, MOD_VERSION
from plugin.installer import setup_game_directory
from voice.meme_player import MemeSoundEngine

VPN_NET_CFG = """// --- AI TEAMMATES MULTIPLAYER VPN TUNING (MP14) ---
// Protocol 47 standalone GoldSrc MUST keep sv_lan 1 (disabling sv_lan hangs on defunct
// 2004 Speakeasy.net VAC module & aborts New Game loopback). Build 3248 already
// allows all VPN subnets (Tailscale 100.x, ZeroTier, Radmin, LAN) under sv_lan 1.
sv_lan 1
sv_lan_rate 25000
sv_maxrate 25000
sv_minrate 10000
sv_maxupdaterate 60
sv_minupdaterate 20
sv_unlag 1
sv_maxunlag 0.5
sv_allowdownload 1
sv_allowupload 1
sys_ticrate 250
sv_timeout 120
"""

CLIENT_BLOCK_START = "// --- AI TEAMMATES MULTIPLAYER CLIENT CONFIG ---"
CLIENT_BLOCK_END = "// --- END AI TEAMMATES MULTIPLAYER CLIENT CONFIG ---"

SERVER_MP_BLOCK_START = "// --- AI TEAMMATES MOD CONFIG ---"
SERVER_MP_BLOCK_END = "// --- END AI TEAMMATES MOD CONFIG ---"


def generate_secure_rcon_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def ensure_local_config(base_dir: str) -> dict:
    """
    Ensure local `config.json` exists with multiplayer defaults and a unique
    randomly generated `rcon_password` (never stored in tracked repo files — MP10).
    """
    cfg_path = os.path.join(base_dir, "config.json")
    example_path = os.path.join(base_dir, "config.example.json")

    cfg = {}
    if os.path.exists(example_path):
        try:
            with open(example_path, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass

    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            cfg.update(user_cfg)
        except Exception:
            pass

    # MP10: Replace empty or legacy default password with a fresh local secret
    rcon_pw = str(cfg.get("rcon_password", "")).strip()
    if not rcon_pw or rcon_pw in ("czeroai", "CHANGE_ME"):
        rcon_pw = generate_secure_rcon_password(12)
        cfg["rcon_password"] = rcon_pw

    cfg.setdefault("match_name", "CZ AI Teammates Squad Lobby")
    cfg.setdefault("mp_maxplayers", DEFAULT_MAX_PLAYERS)
    cfg.setdefault("mp_bot_mode", "fill")
    cfg.setdefault("mp_bot_count", 8)
    cfg.setdefault("mp_friendly_fire", 0)
    cfg.setdefault("mp_start_map", "de_dust2_cz")
    cfg.setdefault("ingame_voice_key", "k")

    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    return cfg


def write_multiplayer_secret_cfg(czero_dir: str, rcon_password: str, match_name: str = "CZ AI Teammates Squad Lobby", bot_mode: str = "fill", bot_count: int = 8, friendly_fire: int = 0) -> str:
    """
    Write local-only `czero/multiplayer_secret.cfg` (gitignored per MP10).
    """
    mode_map = {"off": 0, "fill": 1, "always": 2}
    mode_int = mode_map.get(str(bot_mode).lower().strip(), 1)
    safe_name = str(match_name).replace('"', "'").strip() or "CZ AI Teammates Squad Lobby"
    safe_pw = str(rcon_password).replace('"', "").strip()

    secret_path = os.path.join(czero_dir, "multiplayer_secret.cfg")
    content = (
        "// Local-only multiplayer host configuration & RCON secret (gitignored - MP10)\n"
        f'rcon_password "{safe_pw}"\n'
        f'hostname "{safe_name}"\n'
        f'ai_match_name "{safe_name}"\n'
        f"ai_mp_bot_mode {mode_int}\n"
        f"ai_mp_bot_target {int(bot_count)}\n"
        f"mp_friendlyfire {1 if friendly_fire else 0}\n"
    )
    with open(secret_path, "w", encoding="latin-1") as f:
        f.write(content)
    return secret_path


def _upsert_managed_block(file_path: str, start_marker: str, end_marker: str, block_body: str):
    existing = ""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="latin-1", errors="ignore") as f:
            existing = f.read()

    # Strip any hardcoded rcon_password from tracked server cfg files (MP10)
    existing = re.sub(r'^\s*rcon_password\s+"[^"]*"\s*$', "", existing, flags=re.MULTILINE)

    full_block = f"{start_marker}\n{block_body.strip()}\n{end_marker}\n"
    if start_marker in existing and end_marker in existing:
        pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker) + r"\n?", re.DOTALL)
        updated = pattern.sub(full_block, existing)
    elif start_marker in existing:
        idx = existing.index(start_marker)
        updated = existing[:idx].rstrip() + "\n\n" + full_block
    else:
        updated = existing.rstrip() + "\n\n" + full_block

    with open(file_path, "w", encoding="latin-1") as f:
        f.write(updated.lstrip() if not existing.strip() else updated)


def write_client_userconfig(czero_dir: str, voice_key: str = "k") -> str:
    """
    Configure `czero/userconfig.cfg` with:
      - MP03 mod version `setinfo "ai_mod_ver" "2.0.0-MP"`
      - MP11 built-in voice settings + push-to-talk key (`k` by default, keeping `v` free for AI mic)
      - MP14 VPN network rates (`rate 25000`, `cl_updaterate 60`, `cl_cmdrate 60`, `ex_interp 0.05`)
    """
    safe_key = (voice_key or "k").strip().replace('"', "") or "k"
    usercfg_path = os.path.join(czero_dir, "userconfig.cfg")
    body = f"""setinfo "ai_mod_ver" "{MOD_VERSION}"
rate "25000"
cl_updaterate "60"
cl_cmdrate "60"
ex_interp "0.05"
cl_dlmax "512"
cl_allowdownload "1"
voice_enable "1"
voice_modenable "1"
voice_scale "1.0"
voice_forcemicrecord "1"
tutor_enable "0"
bind "{safe_key}" "+voicerecord"
"""
    _upsert_managed_block(usercfg_path, CLIENT_BLOCK_START, CLIENT_BLOCK_END, body)

    # Ensure config.cfg ends with `exec userconfig.cfg`
    cfg_path = os.path.join(czero_dir, "config.cfg")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="latin-1", errors="ignore") as f:
            c_text = f.read()
        if "exec userconfig.cfg" not in c_text.lower():
            with open(cfg_path, "a", encoding="latin-1") as f:
                f.write("\nexec userconfig.cfg\n")

    return usercfg_path


def write_server_configs(czero_dir: str):
    """
    Write `czero/vpn_net.cfg` and update `czero/listenserver.cfg` & `czero/server.cfg`
    without storing any secrets in tracked `.cfg` files (MP05, MP10, MP11, MP14).
    """
    vpn_cfg_path = os.path.join(czero_dir, "vpn_net.cfg")
    with open(vpn_cfg_path, "w", encoding="latin-1") as f:
        f.write(VPN_NET_CFG)

    server_block = """log on
mp_logdetail 3
mp_logecho 1
mp_logfile 1
logaddress_delall
logaddress_add 127.0.0.1 27115
bot_chatter "off"
bot_defer_to_human 1
bot_auto_vacate 1
allow_spectators 1
sv_voiceenable 1
sv_voicecodec "voice_speex"
sv_voicequality 5
sv_alltalk 1
pausable 1
exec vpn_net.cfg
exec multiplayer_secret.cfg"""

    for cfg_name in ("listenserver.cfg", "server.cfg"):
        cfg_file = os.path.join(czero_dir, cfg_name)
        _upsert_managed_block(cfg_file, SERVER_MP_BLOCK_START, SERVER_MP_BLOCK_END, server_block)


TUTOR_SCHEME_RES = """//
// AI TEAMMATES CHAT OVERLAY SCHEME (Low-Opacity Black Background)
//
Scheme
{
\t//////////////////////// COLORS ///////////////////////////
\tColors
\t{
\t\t// Low-opacity black background (~45% opacity: 115 / 255) behind bot chat text
\t\t"WindowBG"\t\t\t\t"0 0 0 115"
\t\t"ControlBG"\t\t\t\t"0 0 0 0"
\t\t"BorderBright"\t\t\t"0 0 0 70"
\t\t"BorderDark"\t\t\t"0 0 0 70"
\t\t"BaseText"\t\t\t\t"245 245 245 255"
\t\t"ControlText"\t\t\t"245 245 245 255"

\t\t// High-contrast team & sound colors on top of the low-opacity black backdrop
\t\t"TutorTextClassDefault"\t"245 245 245 255"\t// Default crisp off-white
\t\t"TutorTextClass2"\t\t"255 135 130 255"\t// Terrorist Warm Red
\t\t"TutorTextClass4"\t\t"155 215 255 255"\t// Counter-Terrorist Ice Blue
\t\t"TutorTextClass8"\t\t"145 245 160 255"\t// Sound / System Mint Green
\t\t"TutorTextClass256"\t\t"255 225 100 255"\t// Match Notice Gold
\t}

\t///////////////////// BASE SETTINGS ////////////////////////
\tBaseSettings
\t{
\t\t"FgColor"\t\t\t"TutorTextClassDefault"
\t\t"BgColor"\t\t\t"ControlBG"
\t\t"LabelBgColor"\t\t"ControlBG"
\t\t"SubPanelBgColor"\t"ControlBG"
\t\t"WindowFgColor"\t\t"TutorTextClassDefault"
\t\t"WindowBgColor"\t\t"WindowBG"
\t\t"ChatBgColor"\t\t"WindowBG"
\t}

\t//////////////////////// FONTS /////////////////////////////
\tFonts
\t{
\t\t"Default"
\t\t{
\t\t\t"1"
\t\t\t{
\t\t\t\t"name"\t\t\t"Verdana"
\t\t\t\t"tall"\t\t\t"13"
\t\t\t\t"weight"\t\t"600"
\t\t\t\t"yres"\t\t\t"480 599"
\t\t\t\t"dropshadow"\t"1"
\t\t\t}
\t\t\t"2"
\t\t\t{
\t\t\t\t"name"\t\t\t"Verdana"
\t\t\t\t"tall"\t\t\t"14"
\t\t\t\t"weight"\t\t"600"
\t\t\t\t"yres"\t\t\t"600 767"
\t\t\t\t"dropshadow"\t"1"
\t\t\t}
\t\t\t"3"
\t\t\t{
\t\t\t\t"name"\t\t\t"Verdana"
\t\t\t\t"tall"\t\t\t"15"
\t\t\t\t"weight"\t\t"600"
\t\t\t\t"yres"\t\t\t"768 1023"
\t\t\t\t"antialias"\t\t"1"
\t\t\t\t"dropshadow"\t"1"
\t\t\t}
\t\t\t"4"
\t\t\t{
\t\t\t\t"name"\t\t\t"Verdana"
\t\t\t\t"tall"\t\t\t"18"
\t\t\t\t"weight"\t\t"600"
\t\t\t\t"yres"\t\t\t"1024 6000"
\t\t\t\t"antialias"\t\t"1"
\t\t\t\t"dropshadow"\t"1"
\t\t\t}
\t\t}
\t}

\t//////////////////// BORDERS //////////////////////////////
\tBorders
\t{
\t\tBaseBorder
\t\t{
\t\t\t"inset" "0 0 1 1"
\t\t\tLeft
\t\t\t{
\t\t\t\t"1"
\t\t\t\t{
\t\t\t\t\t"color" "BorderDark"
\t\t\t\t\t"offset" "0 1"
\t\t\t\t}
\t\t\t}
\t\t\tRight
\t\t\t{
\t\t\t\t"1"
\t\t\t\t{
\t\t\t\t\t"color" "BorderBright"
\t\t\t\t\t"offset" "1 0"
\t\t\t\t}
\t\t\t}
\t\t\tTop
\t\t\t{
\t\t\t\t"1"
\t\t\t\t{
\t\t\t\t\t"color" "BorderDark"
\t\t\t\t\t"offset" "0 0"
\t\t\t\t}
\t\t\t}
\t\t\tBottom
\t\t\t{
\t\t\t\t"1"
\t\t\t\t{
\t\t\t\t\t"color" "BorderBright"
\t\t\t\t\t"offset" "0 0"
\t\t\t\t}
\t\t\t}
\t\t}
\t}
}
"""

TUTOR_WINDOW_RES = """"Resource/UI/TutorTextWindow.res"
{
\t"TutorTextWindow"
\t{
\t\t"ControlName"\t\t"Frame"
\t\t"fieldName"\t\t"TutorTextWindow"
\t\t"xpos"\t\t"0"
\t\t"ypos"\t\t"0"
\t\t"wide"\t\t"290"
\t\t"tall"\t\t"110"
\t\t"autoResize"\t\t"0"
\t\t"pinCorner"\t\t"0"
\t\t"visible"\t\t"1"
\t\t"enabled"\t\t"1"
\t\t"tabPosition"\t\t"0"
\t\t"settitlebarvisible"\t\t"0"
\t}
\t"TopLeftPanel"
\t{
\t\t"ControlName"\t\t"Panel"
\t\t"fieldName"\t\t"TopLeftPanel"
\t\t"xpos"\t\t"0"
\t\t"ypos"\t\t"0"
\t\t"wide"\t\t"4"
\t\t"tall"\t\t"4"
\t\t"autoResize"\t\t"0"
\t\t"pinCorner"\t\t"0"
\t\t"visible"\t\t"0"
\t\t"enabled"\t\t"0"
\t\t"tabPosition"\t\t"0"
\t}
\t"TopRightPanel"
\t{
\t\t"ControlName"\t\t"Panel"
\t\t"fieldName"\t\t"TopRightPanel"
\t\t"xpos"\t\t"286"
\t\t"ypos"\t\t"0"
\t\t"wide"\t\t"4"
\t\t"tall"\t\t"4"
\t\t"autoResize"\t\t"0"
\t\t"pinCorner"\t\t"0"
\t\t"visible"\t\t"0"
\t\t"enabled"\t\t"0"
\t\t"tabPosition"\t\t"0"
\t}
\t"BottomLeftPanel"
\t{
\t\t"ControlName"\t\t"Panel"
\t\t"fieldName"\t\t"BottomLeftPanel"
\t\t"xpos"\t\t"0"
\t\t"ypos"\t\t"106"
\t\t"wide"\t\t"4"
\t\t"tall"\t\t"4"
\t\t"autoResize"\t\t"0"
\t\t"pinCorner"\t\t"0"
\t\t"visible"\t\t"0"
\t\t"enabled"\t\t"0"
\t\t"tabPosition"\t\t"0"
\t}
\t"BottomRightPanel"
\t{
\t\t"ControlName"\t\t"Panel"
\t\t"fieldName"\t\t"BottomRightPanel"
\t\t"xpos"\t\t"286"
\t\t"ypos"\t\t"106"
\t\t"wide"\t\t"4"
\t\t"tall"\t\t"4"
\t\t"autoResize"\t\t"0"
\t\t"pinCorner"\t\t"0"
\t\t"visible"\t\t"0"
\t\t"enabled"\t\t"0"
\t\t"tabPosition"\t\t"0"
\t}
\t"IconPanel"
\t{
\t\t"ControlName"\t\t"Panel"
\t\t"fieldName"\t\t"IconPanel"
\t\t"xpos"\t\t"2"
\t\t"ypos"\t\t"2"
\t\t"wide"\t\t"1"
\t\t"tall"\t\t"1"
\t\t"autoResize"\t\t"0"
\t\t"pinCorner"\t\t"0"
\t\t"visible"\t\t"0"
\t\t"enabled"\t\t"0"
\t\t"tabPosition"\t\t"0"
\t}
\t"GapPanel"
\t{
\t\t"ControlName"\t\t"Panel"
\t\t"fieldName"\t\t"GapPanel"
\t\t"xpos"\t\t"4"
\t\t"ypos"\t\t"0"
\t\t"wide"\t\t"1"
\t\t"tall"\t\t"110"
\t\t"autoResize"\t\t"0"
\t\t"pinCorner"\t\t"0"
\t\t"visible"\t\t"0"
\t\t"enabled"\t\t"0"
\t\t"tabPosition"\t\t"0"
\t}
\t"TutorMessageLabel"
\t{
\t\t"ControlName"\t\t"Label"
\t\t"fieldName"\t\t"TutorMessageLabel"
\t\t"xpos"\t\t"10"
\t\t"ypos"\t\t"8"
\t\t"wide"\t\t"270"
\t\t"tall"\t\t"94"
\t\t"autoResize"\t\t"0"
\t\t"pinCorner"\t\t"0"
\t\t"visible"\t\t"1"
\t\t"enabled"\t\t"1"
\t\t"tabPosition"\t\t"0"
\t\t"labelText"\t\t""
\t\t"textAlignment"\t\t"north-west"
\t\t"dulltext"\t\t"0"
\t\t"brighttext"\t\t"0"
\t\t"wrap"\t\t"1"
\t}
}
"""


def write_chat_backdrop_ui(base_dir: str):
    """
    Configure Condition Zero's VGUI2 chat readability & low-opacity black chat background:
      1. `czero/resource/ClientScheme.res` — sets `"WindowBG" "0 0 0 115"` and adds crisp
         `"dropshadow" "1"` on `"Default"` & `"EngineFont"` for bottom-left HUD SayText.
      2. `czero/resource/TutorScheme.res` & `czero/resource/UI/TutorTextWindow.res` — styles
         Condition Zero's native translucent VGUI2 panel with a low-opacity black background
         (`rgba(0, 0, 0, 115)`) behind rolling bot chat lines.
      3. `czero/sound/events/tutor_msg.wav` — overrides the default tutor chime with silence
         so updating the low-opacity black chat box never plays unwanted UI beeps.
    """
    czero_dir = os.path.join(base_dir, "czero")
    cstrike_scheme = os.path.join(base_dir, "cstrike", "resource", "ClientScheme.res")
    czero_res_dir = os.path.join(czero_dir, "resource")
    czero_ui_dir = os.path.join(czero_res_dir, "UI")
    czero_scheme = os.path.join(czero_res_dir, "ClientScheme.res")

    if os.path.exists(czero_res_dir):
        os.makedirs(czero_ui_dir, exist_ok=True)
        with open(os.path.join(czero_res_dir, "TutorScheme.res"), "w", encoding="latin-1") as f:
            f.write(TUTOR_SCHEME_RES)
        with open(os.path.join(czero_ui_dir, "TutorTextWindow.res"), "w", encoding="latin-1") as f:
            f.write(TUTOR_WINDOW_RES)

        # Silent 40ms 16-bit 22050 Hz mono PCM WAV so TutorText opens silently
        events_snd_dir = os.path.join(czero_dir, "sound", "events")
        os.makedirs(events_snd_dir, exist_ok=True)
        silent_wav = os.path.join(events_snd_dir, "tutor_msg.wav")
        with wave.open(silent_wav, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            wf.writeframes(b"\x00\x00" * 882)

    if not os.path.exists(cstrike_scheme) or not os.path.exists(czero_res_dir):
        return

    with open(cstrike_scheme, "r", encoding="latin-1", errors="ignore") as f:
        src = f.read()

    # Low-opacity black background (~45% opacity) for chat panes
    src = re.sub(r'"WindowBG"\s+"0 0 0 \d+"', '"WindowBG"\t\t\t"0 0 0 115"', src)

    # Upgrade Default font tiers + add EngineFont with dropshadow "1" for HUD SayText readability
    default_and_engine_fonts = '''\t\t"Default"
\t\t{
\t\t\t"1"
\t\t\t{
\t\t\t\t"name"\t\t"Verdana"
\t\t\t\t"tall"\t\t"13"
\t\t\t\t"weight"\t"700"
\t\t\t\t"yres"\t"480 599"
\t\t\t\t"dropshadow"\t"1"
\t\t\t}
\t\t\t"2"
\t\t\t{
\t\t\t\t"name"\t\t"Verdana"
\t\t\t\t"tall"\t\t"14"
\t\t\t\t"weight"\t"700"
\t\t\t\t"yres"\t"600 767"
\t\t\t\t"dropshadow"\t"1"
\t\t\t}
\t\t\t"3"
\t\t\t{
\t\t\t\t"name"\t\t"Verdana"
\t\t\t\t"tall"\t\t"15"
\t\t\t\t"weight"\t"700"
\t\t\t\t"yres"\t"768 1023"
\t\t\t\t"antialias"\t"1"
\t\t\t\t"dropshadow"\t"1"
\t\t\t}
\t\t\t"4"
\t\t\t{
\t\t\t\t"name"\t\t"Verdana"
\t\t\t\t"tall"\t\t"20"
\t\t\t\t"weight"\t"700"
\t\t\t\t"yres"\t"1024 1199"
\t\t\t\t"antialias"\t"1"
\t\t\t\t"dropshadow"\t"1"
\t\t\t}
\t\t\t"5"
\t\t\t{
\t\t\t\t"name"\t\t"Verdana"
\t\t\t\t"tall"\t\t"24"
\t\t\t\t"weight"\t"700"
\t\t\t\t"yres"\t"1200 6000"
\t\t\t\t"antialias"\t"1"
\t\t\t\t"dropshadow"\t"1"
\t\t\t}
\t\t}
\t\t"EngineFont"
\t\t{
\t\t\t"1"
\t\t\t{
\t\t\t\t"name"\t\t"Verdana"
\t\t\t\t"tall"\t\t"13"
\t\t\t\t"weight"\t"700"
\t\t\t\t"yres"\t"480 599"
\t\t\t\t"dropshadow"\t"1"
\t\t\t}
\t\t\t"2"
\t\t\t{
\t\t\t\t"name"\t\t"Verdana"
\t\t\t\t"tall"\t\t"15"
\t\t\t\t"weight"\t"700"
\t\t\t\t"yres"\t"600 767"
\t\t\t\t"dropshadow"\t"1"
\t\t\t}
\t\t\t"3"
\t\t\t{
\t\t\t\t"name"\t\t"Verdana"
\t\t\t\t"tall"\t\t"16"
\t\t\t\t"weight"\t"700"
\t\t\t\t"yres"\t"768 1023"
\t\t\t\t"dropshadow"\t"1"
\t\t\t}
\t\t\t"4"
\t\t\t{
\t\t\t\t"name"\t\t"Verdana"
\t\t\t\t"tall"\t\t"20"
\t\t\t\t"weight"\t"700"
\t\t\t\t"yres"\t"1024 1199"
\t\t\t\t"dropshadow"\t"1"
\t\t\t}
\t\t\t"5"
\t\t\t{
\t\t\t\t"name"\t\t"Verdana"
\t\t\t\t"tall"\t\t"24"
\t\t\t\t"weight"\t"700"
\t\t\t\t"yres"\t"1200 6000"
\t\t\t\t"dropshadow"\t"1"
\t\t\t}
\t\t}
\t\t"DefaultUnderline"'''

    src = re.sub(
        r'\t\t"Default"\s*\{.*?\n\t\t\}\s*\t\t"DefaultUnderline"',
        default_and_engine_fonts,
        src,
        count=1,
        flags=re.DOTALL,
    )

    with open(czero_scheme, "w", encoding="latin-1") as f:
        f.write(src)


def install_multiplayer(base_dir: str | None = None) -> dict:
    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    czero_dir = os.path.join(base_dir, "czero")

    print("=================================================================")
    print(f"  INSTALLING CZ AI TEAMMATES + MULTIPLAYER MOD ({MOD_VERSION})")
    print("=================================================================")

    # 1. Base Metamod + AMX Mod X + BotProfile setup
    setup_game_directory(czero_dir)

    # 2. Local config & secret RCON generation (MP10)
    cfg = ensure_local_config(base_dir)

    # 3. Server & VPN configs (MP05, MP10, MP11, MP14)
    write_server_configs(czero_dir)
    secret_path = write_multiplayer_secret_cfg(
        czero_dir=czero_dir,
        rcon_password=cfg["rcon_password"],
        match_name=cfg.get("match_name", "CZ AI Teammates Squad Lobby"),
        bot_mode=cfg.get("mp_bot_mode", "fill"),
        bot_count=cfg.get("mp_bot_count", 8),
        friendly_fire=cfg.get("mp_friendly_fire", 0),
    )

    # 4. Client userconfig & low-opacity black chat backdrop UI (MP03, MP11, MP14)
    voice_key = cfg.get("ingame_voice_key", "k")
    usercfg_path = write_client_userconfig(czero_dir, voice_key=voice_key)
    write_chat_backdrop_ui(base_dir)

    # 5. Prepare 16-bit 22050 Hz mono GoldSrc WAV sound bank
    MemeSoundEngine(base_dir=base_dir, enabled=True)

    print(f"[MP Setup] Mod Version       : {MOD_VERSION}")
    print(f"[MP Setup] VPN Tuning        : {os.path.join(czero_dir, 'vpn_net.cfg')}")
    print(f"[MP Setup] Client Config     : {usercfg_path} (Voice PTT bound to '{voice_key.upper()}')")
    print(f"[MP Setup] Local Host Secret : {secret_path} (gitignored)")
    print("=================================================================")
    print("  SETUP COMPLETE!")
    print("  - To HOST a match for friends : Run host.bat")
    print("  - To JOIN a friend's match    : Run join.bat")
    print("  - To CHECK VPN & ping         : py check_vpn.py <host_vpn_ip>")
    print("=================================================================")
    return cfg


if __name__ == "__main__":
    install_multiplayer()
    sys.exit(0)

