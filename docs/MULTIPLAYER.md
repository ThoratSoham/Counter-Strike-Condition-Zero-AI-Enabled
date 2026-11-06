# Multiplayer Guide: Play with 10+ Real Friends Over Free VPN (Section 19)

Play **Counter-Strike: Condition Zero** with **10 to 32 real human friends** over the internet with **zero router port forwarding**, **built-in voice chat**, and **AI Bot Teammates (Vikram, Kabir, Marcus, Sunny)** who roast your friends, hype big plays, and fill empty slots automatically.

---

## 1. Free VPN Comparison for 10+ Friends (`MP0`)

Condition Zero uses UDP port `27015`. A free mesh VPN gives everyone a private virtual LAN IP so any friend can host without touching router settings:

| VPN App | Free Limit for Gaming Squads | Latency / Architecture | Setup for 10–30 Friends |
| :--- | :--- | :--- | :--- |
| **Tailscale** *(Recommended)* | **100 devices** (3 users on one tailnet + **unlimited external friends via free Node Sharing**) | Peer-to-peer WireGuard (`100.64.x.y`), lowest ping | Host shares their machine link with each friend's free Tailscale account, or friends sign into a shared squad tailnet. |
| **ZeroTier** | **Up to 25 devices** per free network | Peer-to-peer VL1 (`10.x` / `172.x`), low ping | Create 1 Network ID at `my.zerotier.com`, share the 16-digit Network ID with up to 24 friends, and check "Auth". |
| **Radmin VPN** *(Windows-only alternative)* | Unlimited peers per room | Virtual LAN (`26.x.y.z`) | Create a room name + password; friends join the room on Windows. |

Check your VPN status and ping to the host at any time:
```powershell
py check_vpn.py
py check_vpn.py <host_vpn_ip>
```

---

## 2. One-Time Setup (`install.bat`)

Both the **Host** and **Joining Friends** run `install.bat` once after cloning/extracting the game folder:
```bat
install.bat
```
What `install.bat` does (`MP2`, `MP03`, `MP10`, `MP11`, `MP14`):
1. Hooks Metamod & AMX Mod X (`czero_ai_teammates.amxx` `v2.0.0-MP`).
2. Generates a unique random RCON password in local `config.json` and writes gitignored `czero/multiplayer_secret.cfg` (**secrets are never stored in Git** — `MP10`).
3. Writes `czero/vpn_net.cfg` (`sv_maxrate 25000`, `sv_maxupdaterate 60`, `sv_unlag 1`) tuned for VPN tunnels (`MP14`).
4. Configures `czero/userconfig.cfg` with client version tag `ai_mod_ver "2.0.0-MP"` (`MP03`), VPN rates, and in-game push-to-talk bound to **`K`** (`MP11`).
5. Ensures all 78 meme sounds in `czero/sound/ai_teammates/` are formatted as 16-bit 22050 Hz mono GoldSrc WAVs.

---

## 3. Hosting a Match (`host.bat` — `MP01`)

**Only the Host runs the AI Brain.** Friends who join do **not** need a Google API key and do **not** run Python/Brain processes.

### Host & Play in Same Window (Listen Server — Default)
Double-click **`host.bat`** (or run from PowerShell):
```powershell
.\host.bat
```

### Dedicated Server Mode (24–32 Slots, Lower CPU Overhead)
```powershell
.\host.bat --dedicated --maxplayers 24 --map de_dust2_cz --bot-mode fill --bots 8 --match-name "Friday Night CZ Squad"
```

When `host.bat` starts, it detects your Tailscale/ZeroTier IP and prints:
```text
>>> SHARE THIS WITH YOUR FRIENDS <<<
    Option A (Easy)   : Double-click join.bat and enter:  100.84.12.5
    Option B (Console): Open ~ console and type:          connect 100.84.12.5:27015
```

> **Windows Firewall Note**: The first time `hl.exe` or `hlds.exe` opens, click **Allow access** on both Private and Public networks so UDP port `27015` can accept VPN traffic.

---

## 4. Joining a Friend's Match (`join.bat` — `MP02`)

1. Connect to the same Tailscale / ZeroTier VPN as the host.
2. Double-click **`join.bat`**.
3. Paste the Host's VPN IP (e.g. `100.84.12.5`). `join.bat` remembers the last IP in `.last_host.txt` so next time you just press **Enter**!
4. `join.bat` pings the server, shows the live map & player count, configures your voice & network settings, and launches Condition Zero directly into the match **without** starting a local AI Brain.

**Missing Sound Safety (`19.4`)**: Sounds are played via client-side `spk` without forced `precache_sound` downloads — if a friend joins without a custom `.wav` file, their game quietly skips the missing sound and **never disconnects**.

---

## 5. Voice Chat & Mic Testing (`MP11`)

- **Talk to Real Friends (`K` key)**: Hold **`K`** in-game (`+voicerecord`) to talk to all friends via Condition Zero's built-in Speex voice codec (`sv_voiceenable 1`, `sv_voicequality 5`).
- **Host Talk to AI Bots (`V` key)**: On the Host PC, **`V`** remains dedicated to Whisper push-to-talk for AI bots — zero key collision with **`K`**.
- **Test Your Mic In-Game**: Type `!mictest` (or console `ai_voice_test`) to hear your own microphone played back for 8 seconds (`voice_loopback 1`), then automatically return to normal match comms.

---

## 6. All Multiplayer Commands (`MP03`–`MP15`)

### Player Chat Commands (`Y` or `U`)
| Command | Feature | Description |
| :--- | :--- | :--- |
| `!match` / `/match` | `MP04` | **(Host)** Opens interactive **Match Setup Menu** (Map, Max Rounds, Friendly Fire, AI Bot Mode `Off`/`Fill`/`Always N`, Bot Count, Chat Style `Clean`/`Banter`/`Full gamer`, Voice AllTalk, Restart). |
| `!admin` / `/admin` | `MP08` | **(Host)** Opens **Admin Control Menu** (Restart, Balance 10+ Teams, Map Vote, Pause/Unpause, Kick Player). |
| `!votemap` / `/rtv` | `MP09` | Starts a 15-second **8-Map Vote Menu** for all human players (also runs automatically at end of `mp_maxrounds`). |
| `!ping` / `/ping` | `MP15` | Displays live VPN ping (ms) and packet loss (%) for every connected human friend. |
| `!mictest` | `MP11` | Enables 8-second self-loopback mic test so you can check mic volume in-game. |
| `!voice` | `MP11` | Prints voice push-to-talk key (`K`) and volume commands (`voice_scale`). |
| `/spec` & `/join` | `MP05` | Move to Spectator (`/spec`) or jump back into an active squad (`/join`). |
| `!balance` | `MP05` | **(Host)** Balances human teams when 10+ players are uneven (also auto-checked at round start). |
| `!sounds` / `!roast` / `!hype` | `19.4` | Opens the Voice Pack menu or triggers attributed meme sounds for everyone in the server. |

### Host Console Commands (`~`)
- `ai_match_menu` — Interactive match setup menu (`MP04`)
- `ai_admin_menu` — Interactive admin menu (`MP08`)
- `ai_kick <name|#userid>` — Kick a player (`MP08`)
- `ai_ban <name> [minutes]` — Ban a player IP for `N` minutes (`MP08`)
- `ai_map <mapname>` — Change map immediately, e.g. `ai_map de_inferno_cz` (`MP08`)
- `ai_restart` — Restart round (`sv_restart 1`) (`MP08`)
- `ai_pause` — Pause / resume the match (`MP08`)
- `ai_balance` — Balance human teams (`MP05`)
- `ai_votemap` — Launch map vote (`MP09`)
- `ai_ping` — Full player ping & packet loss table (`MP15`)

