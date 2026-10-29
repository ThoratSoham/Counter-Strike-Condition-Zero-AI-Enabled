# STEP 1: Current System Status Audit (`docs/STATUS.md`)

Audit performed against the live workspace (`E:\CZero VibeCoding`) and game/AMXX logs (`czero/addons/amxmodx/logs/`, `czero/logs/L1027002.log`, `czero/logs/mod.log`, and `logs/mod.log`).

---

## 1. Is there an in-game plugin (`.amxx` or Metamod `.dll`) in the `czero` folder? Where is it?

**Yes.** Both Metamod and AMX Mod X are installed inside `czero/addons/`, along with the custom AMX Mod X plugin:

- **Metamod DLL**:
  - `czero/addons/metamod/dlls/metamod.dll`
- **AMX Mod X Metamod DLL**:
  - `czero/addons/amxmodx/dlls/amxmodx_mm.dll` (AMX Mod X v1.10.0.5487)
- **AMX Mod X Modules** (`czero/addons/amxmodx/modules/`):
  - `cstrike_amxx.dll`, `engine_amxx.dll`, `fakemeta_amxx.dll`, `fun_amxx.dll`, `sockets_amxx.dll`, `regex_amxx.dll`, `hamsandwich_amxx.dll`, `nvault_amxx.dll`, `json_amxx.dll`, `csx_amxx.dll`
- **Compiled Custom AMX Mod X Plugin (`.amxx`)**:
  - `czero/addons/amxmodx/plugins/czero_ai_teammates.amxx`
  - Also present in `czero/addons/amxmodx/scripting/czero_ai_teammates.amxx` and `czero/addons/amxmodx/scripting/compiled/czero_ai_teammates.amxx`
- **Plugin Source Code (`.sma`)**:
  - `czero/addons/amxmodx/scripting/czero_ai_teammates.sma`
  - Duplicate copy in `plugin/amxx/ai_teammates.sma`

---

## 2. Is it loaded? (`plugins.ini`, `meta list`, `amx_plugins` / game logs)

**Yes, Metamod, AMX Mod X, and `czero_ai_teammates.amxx` are configured and load when `hl.exe -game czero` starts**, as verified by the configuration files and actual game logs:

1. **`czero/liblist.gam` (Line 14)**:
   - Points to Metamod: `gamedll "addons\metamod\dlls\metamod.dll"`
2. **`czero/addons/metamod/plugins.ini` (Line 2)**:
   - Loads AMX Mod X: `win32 addons\amxmodx\dlls\amxmodx_mm.dll`
3. **`czero/addons/amxmodx/configs/plugins.ini` (Line 47)**:
   - Loads the plugin: `czero_ai_teammates.amxx`
4. **Confirmed in Game Logs (`czero/logs/mod.log` & `czero/logs/L1027002.log`)**:
   - `czero/logs/mod.log` confirms `plugin_init()` executed inside `hl.exe`:
     `[Step 1] Plugin loaded (Metamod 'meta list' shows it). AMX Mod X hook initialized.`
   - However, two critical bugs prevented chat from showing properly on screen:
     1. In `czero/addons/amxmodx/logs/L20261027.log`, `czero/dlls/mp.dll` has a gamedata CRC mismatch with AMXX 1.10's default `cstrike` gamedata, and when the earlier plugin called `engclient_cmd(bot_id, "say_team", ...)` (`czero/logs/L1027002.log` line 51: `"Niles<2><BOT><TERRORIST>" say_team "Hell yeah! Let's wipe these clowns!"`), it picked `Niles` (a **TERRORIST** bot) while the human player (`Player<1>`) was on **CT**—and GoldSrc hides opposing-team `say_team` messages and dead-bot `say_team` messages from living players!
     2. In `czero_ai_teammates.sma`, `connect_to_brain()` only sent `PING|init` once on map load and only retried if `g_lastBrainHeartbeat` changed, instead of sending a continuous `"game alive"` heartbeat every 2 seconds.

---

## 3. How does the brain talk to the game right now?

Currently, communication uses **UDP on `127.0.0.1:27115`** (plus a GoldSrc RCON fallback on port `27015`):

1. **Plugin -> Brain (UDP `127.0.0.1:27115`)**:
   - `czero_ai_teammates.sma` uses the AMX Mod X `sockets` module (`socket_open("127.0.0.1", 27115, SOCKET_UDP, err, SOCK_NON_BLOCKING)`) to send text packets (`PING|init`, `EVENT|chat|...`, `EVENT|kill|...`, `EVENT|round_start`, etc.) to `GameBridge` (`plugin/game_bridge.py`).
   - `czero/listenserver.cfg` also configures `logaddress_add 127.0.0.1 27115`, which streams raw GoldSrc server log lines over UDP to port `27115`.
2. **Brain -> Plugin (UDP reply to `self.plugin_addr`)**:
   - `GameBridge.send_to_plugin()` sends UDP packets (`PONG`, `SAY|<bot>|<msg>`, `SOUND|...`, `ORDER|...`, `STATUS|...`) back to the source port of the AMX Mod X UDP socket, which the plugin polls every `0.1s` in `socket_poll_task()`.
3. **Why it failed when running standalone**:
   - `play_czero.bat` only launched `hl.exe` without starting `main.py` (the Brain).
   - `run_ai_teammates.bat` (`py main.py`) launched the Brain without checking if `hl.exe` was running or connected. `ChatterEngine.start()` immediately began firing lines every 10–20 seconds even when `self.game_bridge.plugin_addr` was `None` (no game running), logging `[Step 6] Chat message sent into the game as a bot: ...` to the VS Code terminal while nothing was connected.

---

## 4. Which program plays the sounds, and what starts it?

**Currently, the external Python process (`main.py` -> `MemeSoundEngine` -> `AudioPlayer`) plays the sounds outside the game using Windows audio (`sounddevice` / `winsound`), NOT the Condition Zero game engine:**

1. **What plays the sounds right now**:
   - `brain/service.py` instantiates `MemeSoundEngine` (`voice/meme_player.py`), which uses `AudioPlayer` (`voice/player.py`).
   - `AudioPlayer` uses the Python `sounddevice` library (with a `winsound.PlaySound` fallback) to play audio directly through the Windows OS mixer.
2. **What starts it**:
   - Running `py main.py` (or `run_ai_teammates.bat`) starts `AIBrainService.start()`, which immediately starts `ChatterEngine._run_loop()` on a background thread.
   - Every 10–20 seconds (or 3–6 seconds during a bot "fight"), `ChatterEngine._run_loop()` pops an idle line from `self.queue` and calls `AIBrainService.dispatch_bot_line()`.
   - Because idle lines in `brain/offline_bank.py` have `sound_tag` values attached, `dispatch_bot_line()` calls `self.meme_sound.play_tag()`, which plays the `.wav` file from `sounds/.cache/<tag>/` via Python's `AudioPlayer`—**even when `hl.exe` is completely closed**.
3. **Are the sounds in `czero/sound/` right now?**:
   - **No.** The normalized 16-bit 22050 Hz mono `.wav` files currently exist only in `E:\CZero VibeCoding\sounds\.cache\<tag>\` (outside `czero/sound/`). None of the meme sound files have been placed inside `czero/sound/` yet.

