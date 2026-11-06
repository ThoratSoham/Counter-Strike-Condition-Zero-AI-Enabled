# Horror "Monster Hunt" Mode for Counter-Strike: Condition Zero

## 1. Overview
The **Horror "Monster Hunt" Mode** transforms Counter-Strike: Condition Zero into an asymmetrical survival horror cooperative experience. A terrifying Half-Life Zombie boss awakens with intelligent adaptive tracking, dynamic combat difficulty presets, lethal signature abilities, and a multi-layered horror UI. Teammate bots dynamically cooperate, kite backwards, and announce sightings over radio, while survivors struggle to survive the night.

---

## 2. File Architecture & Installed Assets

All required models, sounds, sprites, plugins, and configs are installed in `czero\`:

```
czero/
├── models/
│   ├── zombie.mdl              <-- Half-Life Zombie master model
│   ├── zombiet.mdl             <-- Zombie texture companion submodel
│   ├── zombie01.mdl            <-- Sequence group 1 (animations)
│   ├── zombie02.mdl            <-- Sequence group 2 (animations)
│   └── zombie03.mdl            <-- Sequence group 3 (animations)
├── sound/
│   ├── zombie/                 <-- Alert, attack, pain, claw strikes, and custom FX:
│   │   ├── zo_alert10.wav..30  <-- Awakening and phase transition roars
│   │   ├── zo_attack1..2.wav   <-- Melee claw swings
│   │   ├── claw_strike1..3.wav <-- Flesh strike and combo finisher sounds
│   │   ├── spit_launch.wav     <-- Acid spit launch telegraph
│   │   ├── spit_hit.wav        <-- Acid spit impact explosion
│   │   └── jumpscare_sting.wav <-- Loud horror sting for ambush jumpscare
│   ├── player/
│   │   └── heartbeat1.wav      <-- Dynamic proximity heartbeat audio
│   └── weapons/
│       └── explode3.wav        <-- Ground stomp shockwave blast
├── sprites/
│   ├── shockwave.spr           <-- Ground stomp expanding cylinder ring
│   ├── bigspit.spr             <-- Ballistic acid spit projectile
│   ├── zerogxplode.spr         <-- Acid spit impact explosion
│   ├── laserbeam.spr           <-- Waypoint path and bot telemetry debug beams
│   ├── bloodspray.spr          <-- Volumetric blood mist on bullet hit
│   └── blood.spr               <-- Arterial blood jet and droplets
├── addons/amxmodx/
│   ├── plugins/
│   │   └── monster_hunt.amxx   <-- Compiled binary (0 warnings, 0 errors)
│   ├── scripting/
│   │   └── monster_hunt.sma    <-- Upgraded source code
│   └── configs/
│       ├── plugins.ini         <-- Plugin registered: monster_hunt.amxx
│       └── monster_hunt.cfg    <-- Auto-persisted cvars and tuning parameters
```

> [!NOTE]
> In GoldSrc, `models/zombie.mdl` automatically opens its companion sequence files (`zombie01.mdl`–`zombie03.mdl`) directly from disk. Calling `precache_model()` on sequence groups causes fatal `Mod_LoadBrushModel` version errors because sequence groups use the `"IDSQ"` magic header rather than the `"IDST"` model header. The plugin precaches only `models/zombie.mdl`.

---

## 3. Difficulty Presets & Health Phases (Step 2)

### Difficulty Presets (`mh_difficulty` 0..3)
Presets are selectable in the menu (`/horror`) or tuned via console:

| Preset | Health | Speed Mult | Damage Mult | Cooldown Mult | Special Perks |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Easy** (`0`) | 3,000 HP | 0.85x | 0.80x | 1.30x (Slower) | Reduced aggression |
| **Normal** (`1`) | 6,000 HP | 1.00x | 1.00x | 1.00x | Standard horror balance (Default) |
| **Nightmare** (`2`) | 12,000 HP | 1.15x | 1.30x | 0.80x (Faster) | Regenerates 1% HP per 5s out of combat |
| **Custom** (`3`) | `mh_monster_health` | `mh_speed_mult` | `mh_damage_mult` | `mh_cooldown_mult` | Fully customizable in menu |

### Damage Reduction & Hit Multipliers
- **Distance / Lone Attacker Reduction (`mh_dmg_reduction 0.20`)**: Incoming damage to the monster is reduced by 20% if the shooter is beyond 700 units or if only 1 player has attacked in the last 4 seconds. This prevents lone snipers or bots from easily melting the monster.
- **Headshot Multiplier**: Headshots deal **2.0x damage** (`HIT_HEAD`).
- **Grenades Multiplier**: Explosive grenades deal **1.5x damage** (`DMG_GRENADE | DMG_BLAST`).
- **Knife**: Deals standard **1.0x damage**.

### Three Health Phases
The monster's behavior dynamically evolves across 3 phases:
1. **Phase 1: Awakened (100%–66% HP)**:
   - Green Health Bar (`[PHASE 1 - AWAKENED]`).
   - Baseline movement and ability cooldowns.
2. **Phase 2: Enraged (66%–33% HP)**:
   - Yellow Health Bar (`[PHASE 2 - ENRAGED]`).
   - Triggers an enraged awakening roar (`zo_alert20.wav`) and screen shake.
   - Movement speed increased by **+15%**; attack cooldowns reduced by **15%**.
3. **Phase 3: Berserk (<33% HP)**:
   - Flashing Red Health Bar (`[PHASE 3 - BERSERK]`).
   - Triggers a bloodcurdling berserk roar (`zo_alert30.wav`) and heavy screen shake.
   - Movement speed increased by **+30%**; attack cooldowns reduced by **30%**; relentless pursuit.

---

## 4. Adaptive Tracking & Intelligence (Step 3)

The monster operates on a 128-node dynamic waypoint graph with an adaptive cognitive layer:
- **Activity Heat Map**: Every gunshot, footstep, or visual sighting adds activity heat (+25.0) to nearby waypoints. Heat decays by 5% every 3 seconds. When patrolling with no target, the monster automatically investigates the hottest areas first.
- **Hiding Spot Detection**: The AI tracks survivor positions. If a player crouches or stays within 48 units of a waypoint for $>5$ seconds, that waypoint is tagged as a camping spot. When the monster loses line of sight, it sweeps recorded hiding spots before generic wandering.
- **Route Prediction**: When pursuing a fleeing target, the monster calculates the target's forward velocity vector ($target\_vel \times 1.2$) and plots its A* path toward the predicted waypoint rather than trailing behind the player's old position.
- **Flanking Routes**: Every 3rd pursuit attempt, the pathfinder calculates a flanking route by applying a heavy cost penalty (+500.0) to all waypoints visible to survivors. This forces the monster through backdoors, side rooms, and unobserved corridors.
- **Pack Awareness**:
  - If survivors cluster together (average separation $<380$ units), the monster targets the lone straggler furthest from the group.
  - If survivors are split up across the map, it targets the weakest player (lowest current HP).
- **Threat Prioritization**: The monster records damage dealt by every survivor. If the top damage dealer is within 900 units, the monster prioritizes them to neutralize the greatest threat.
- **Sixth Sense**: Periodically pings the approximate location of survivors through walls every 8 seconds (`mh_sense 1`).

---

## 5. Kill Abilities (Step 4)

| Ability | CVar Toggle | Range / Radius | Cooldown | Telegraph & Visuals | Damage & Effects |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Combo Melee** | `mh_ability_combo 1` | $\le 95$ units | 2.0s | Distinct claw sounds for swings 1, 2, and 3 | Swing 1 (38 dmg) $\rightarrow$ Swing 2 (45 dmg) $\rightarrow$ Swing 3 (60 dmg + massive knockback sending victims flying backwards). |
| **Apex Lunge** | `mh_ability_lunge 1` | 350–800 units | 8.0s | 0.45s crouch telegraph, alert roar, airborne leap | Leaps across the gap at 680 u/s; deals 55 dmg on impact and knocks victim down. Followed by a 1.0s stagger recovery opening where players can safely punish it. |
| **Ground Stomp** | `mh_ability_stomp 1` | 350 radius | 12.0s | Heavy foot slam animation, shockwave sound | Spawns an expanding `TE_BEAMCYLINDER` shockwave ring (`shockwave.spr`); deals 28 AoE damage, heavy ScreenShake, and slows all caught players to 130 u/s for 2.0 seconds. |
| **Acid Spit** | `mh_ability_ranged 1` | $>350$ units | 10.0s | 0.5s hiss windup (`spit_launch.wav`) | Used when target is camping or unreachable for $>3$s. Spawns a bouncing ballistic projectile (`bigspit.spr`) that explodes on impact (`spit_hit.wav`, `zerogxplode.spr`) dealing 35 AoE damage in a 150u radius. |
| **Jumpscare** | `mh_jumpscare 1` | $\le 150$ units | 30.0s / player | Triggered when sneaking behind an unaware target | Freezes victim movement for 0.4s, plays loud sting (`jumpscare_sting.wav`), forces victim view toward monster's face, ScreenFade, ScreenShake, followed by an immediate heavy claw hit. |

### Photosensitivity Flash-Safe Mode (`mh_flash_safe`)
- `mh_flash_safe 0`: Full intense red/black fade.
- `mh_flash_safe 1`: Soft dark tint with no sharp strobing for photosensitive players.

### Anti-Repetition Rule
The monster stores its last ability used and will never execute the same special ability twice in a row.

---

## 6. Teammate Bot Brain AI (5Hz)

Teammate bots utilize a dedicated 5Hz finite state machine:
- **`BOT_STATE_SEARCH`**: Disperses bots across distributed waypoint zones (`(id * 7) % total_waypoints`) to sweep rooms instead of clumping. Converges on shared callouts.
- **`BOT_STATE_ENGAGE`**: Holds preferred combat distances based on active weapon:
  - Shotguns: 450 units
  - SMGs: 580 units
  - Rifles: 700 units
  - Snipers: 850 units
  Aims directly at monster upper chest with aim jitter (`mh_bot_aim_error 2.5`), fires in controlled bursts, and locks into combat for at least 8.0s (`mh_bot_commit_time`).
- **`BOT_STATE_KITE`**: When the monster approaches within 420 units (`mh_bot_danger_dist`) or targets the bot, the bot backpedals (-320 u/s) and strafes away while keeping crosshair locked on the monster and continuing defensive fire.
- **`BOT_STATE_PANIC`**: If health drops below 25 HP or cornered with low courage, the bot turns and sprints full speed away.
- **Reaction to Monster Abilities**:
  - Bots immediately retreat when ground stomp windup is detected.
  - Bots strafe sideways to sidestep incoming lunges.
- **Shared Radio Callouts**: When any teammate spots the monster, all bots learn its location for 7.0 seconds and broadcast a radio alert (`mh_bot_callouts 1`).

---

## 7. UI Systems (Step 5)

### 1. Boss Health Bar (Top Center, 4Hz)
Displayed at `-1.0, 0.03` with renderable GoldSrc font characters:
```
ZOMBIE   [||||||||||||||||    ]   78%
[PHASE 1 - AWAKENED]
```
- Green for Phase 1 (>66%), Yellow for Phase 2 (33–66%), Red for Phase 3 (<33%).
- Visible when damaged, within 1200 units, or permanently if `mh_healthbar_always 1`.

### 2. Proximity Danger Meter HUD (Bottom-Left, 3Hz, Channel 3)
Displayed at `0.04, 0.82` when the monster is within 1200 units (`mh_danger_hud 1`):
```
DANGER: [|||| ]   (540u)
DIRECTION: TO YOUR LEFT
```
- Proximity bars scale from `[|    ]` (Faint) up to `[|||||]` (Critical <400u).
- Direction hints dynamically compute relative yaw: `AHEAD`, `TO YOUR LEFT`, `TO YOUR RIGHT`, or `BEHIND YOU!`.

### 3. Round Summary
Printed to chat and displayed on a centered HUD banner at round end (`mh_round_summary 1`):
- Monster health remaining.
- Survivors devoured (Players and Teammate Bots).
- Deadliest monster attack.
- Top damage dealer with total damage dealt.

### 4. Interactive In-Game Menu (`/horror` or `mh_menu`)
Accessible via chat `/horror` or console `mh_menu`:
- **Main Menu**:
  1. Game Mode: [Monster Hunt / Regular Match]
  2. Difficulty: [Easy / Normal / Nightmare / Custom]
  3. Custom Monster Attributes $\rightarrow$ Sub-Menu
  4. Adaptive Tracking & Senses $\rightarrow$ Sub-Menu
  5. Kill Abilities & Attacks $\rightarrow$ Sub-Menu
  6. Teammate Bot AI Settings $\rightarrow$ Sub-Menu
  7. Atmosphere & Immersion $\rightarrow$ Sub-Menu
  8. Spawn Monster / Kill Monster
- **Admin Security**: Only administrators with `ADMIN_CFG` (flag 'c') can change settings. Non-admin players can open the menu in view-only mode.
- **Persistence**: Any change made in the menu is automatically written to `czero\addons\amxmodx\configs\monster_hunt.cfg` so settings persist across map changes.

---

## 8. Console Variables (CVars) Reference

| CVar | Default | Description |
| :--- | :--- | :--- |
| `mh_enabled` | `1` | `1` = Monster Hunt active, `0` = Regular match (vanilla rules and daylight). |
| `mh_difficulty` | `1` | `0` = Easy, `1` = Normal, `2` = Nightmare, `3` = Custom. |
| `mh_monster_health` | `6000.0` | Base hit points for the monster (Custom preset). |
| `mh_speed_mult` | `1.00` | Movement speed multiplier. |
| `mh_damage_mult` | `1.00` | Melee and ability damage multiplier. |
| `mh_cooldown_mult` | `1.00` | Ability attack cooldown multiplier. |
| `mh_dmg_reduction` | `0.20` | Damage reduction when attacker is $>700$u or single shooter (20%). |
| `mh_tracking_mode` | `2` | `0` = Fair, `1` = Relentless, `2` = Adaptive (heat map, hiding spots, flanking). |
| `mh_target_mode` | `0` | `0` = Nearest, `1` = Weakest, `2` = Random, `3` = Lone Player. |
| `mh_prefer_bots` | `0` | `1` = Prioritize bots, `2` = Prioritize humans, `0` = Neutral. |
| `mh_sight_range` | `1500.0` | Monster line of sight vision range. |
| `mh_hear_range` | `1200.0` | Gunshot and movement hearing detection radius. |
| `mh_sense` | `1` | Sixth Sense wall-scanning awareness. |
| `mh_sense_interval` | `8.0` | Seconds between Sixth Sense scans. |
| `mh_ability_combo` | `1` | `1` enables 3-strike combo melee with knockback; `0` disables. |
| `mh_combo_damage` | `38.0` | Base damage for combo melee strike. |
| `mh_ability_lunge` | `1` | `1` enables Apex Lunge / Charge; `0` disables. |
| `mh_lunge_damage` | `55.0` | Impact damage for Apex Lunge. |
| `mh_lunge_cooldown`| `8.0` | Cooldown in seconds between lunges. |
| `mh_ability_stomp` | `1` | `1` enables Ground Stomp shockwave; `0` disables. |
| `mh_stomp_damage` | `28.0` | Ground stomp blast damage. |
| `mh_stomp_radius` | `350.0` | Ground stomp shockwave radius in units. |
| `mh_stomp_cooldown`| `12.0` | Cooldown in seconds between ground stomps. |
| `mh_ability_ranged`| `1` | `1` enables ballistic Acid Spit at out-of-reach targets; `0` disables. |
| `mh_ranged_damage` | `35.0` | AoE explosion damage for acid spit. |
| `mh_ranged_cooldown`| `10.0` | Cooldown in seconds between acid spits. |
| `mh_jumpscare` | `1` | `1` enables sneak ambush jumpscares; `0` disables. |
| `mh_flash_safe` | `0` | `1` softens screen fades for photosensitive players; `0` intense horror. |
| `mh_jumpscare_cooldown`| `30.0`| Seconds cooldown per individual player before jumpscare can trigger again. |
| `mh_healthbar` | `1` | `1` displays top-center boss health bar; `0` disables. |
| `mh_healthbar_always`| `0` | `1` permanently shows health bar; `0` shows when damaged or nearby. |
| `mh_danger_hud` | `1` | `1` displays proximity danger meter HUD with direction hint; `0` disables. |
| `mh_round_summary` | `1` | `1` displays round performance and MVP statistics at round end; `0` disables. |
| `mh_bot_react` | `1` | `1` enables teammate bot combat AI; `0` disables. |
| `mh_bot_ai` | `1` | `1` enables 5Hz advanced bot brain (kiting, burst fire, room sweeps). |
| `mh_bot_danger_dist`| `420.0`| Distance in units at which bots begin backpedal kiting. |
| `mh_bot_commit_time`| `8.0` | Seconds bots stay locked in combat before disengaging. |
| `mh_bot_callouts` | `1` | `1` enables radio callouts when monster is spotted; `0` disables. |
| `mh_blood` | `1` | `1` enables volumetric blood sprays, streams, and decals (no sparks). |
| `mh_blood_color` | `0` | `0` = Visceral Red, `1` = Alien Yellow/Green. |
| `mh_atmosphere` | `1` | `1` enables Dark Midnight lighting ("b"); `0` daylight ("m"). |
| `mh_heartbeat` | `1` | `1` enables proximity heartbeat audio; `0` disables. |
| `mh_debug` | `0` | `1` draws laser beams for A* paths, bot states, and prints telemetry. |

---

## 9. Verification & Testing Checklist

- [x] **Zero Warning Compilation**: Source compiles cleanly with `amxxpc.exe` with 0 errors and 0 warnings.
- [x] **Difficulty Presets**: Switching between Easy (3000 HP), Normal (6000 HP), Nightmare (12000 HP), and Custom scales monster stats accurately.
- [x] **Team of Bots Longevity**: On Normal (6000 HP) and Nightmare (12000 HP) with 20% distance damage reduction, a team of bots cannot melt the monster in under 2 minutes.
- [x] **Adaptive Tracking & Flanking**: Heat map decays naturally, campers are detected, fleeing target routes are predicted, and the monster routes through flanks when survivors cluster.
- [x] **Kill Abilities**:
  - Combo melee delivers 3 successive swings with heavy knockback on the 3rd.
  - Apex Lunge leaps across 350–800u after telegraph roar, with a 1.0s stagger recovery opening.
  - Ground Stomp spawns a shockwave ring, shakes screens, and slows caught survivors for 2.0s.
  - Acid Spit hurls a ballistic projectile that detonates on contact when targets camp out of reach.
  - Jumpscare triggers from behind with a 0.4s freeze, sting sound, and view snap (with flash-safe option).
- [x] **UI & HUD**: Boss health bar displays phase status, danger meter shows distance and direction (`BEHIND YOU!`, `TO YOUR LEFT`, etc.), settings menu saves changes to disk, and round summaries report top killers and damage dealers.
- [x] **Vanilla Mode Integrity**: When `mh_enabled 0` is set, daylight is restored and regular Counter-Strike gameplay is 100% unaffected.

---

## 10. Known Limitations & Technical Quirks (Current Branch)

This branch contains the full Monster Hunt horror gamemode prototype with active bot AI and abilities. The following limitations and known issues are currently present in this build:

1. **Optimization**:
   - The AI state machine, adaptive tracking heuristics (heat maps, player route prediction, flank path calculations), and teammate bot AI ticks run periodically in Pawn. On lower-end systems or high player/bot counts, this can cause CPU spikes or framerate drops.
2. **Monster Textures & Skin Rendering**:
   - Depending on the GoldSrc client renderer, OpenGL version, or video driver settings, the monster's model textures may fail to map or load on some client configurations, causing the zombie to appear as an untextured plain white or grey character model.
3. **Persistent Background Ambience & Audio Loops**:
   - Ambient horror sound effects (wind, eerie droning, and heartbeat proximity audio) may continue playing in the background without cleanly terminating when the round ends or during match resets.
4. **Immediate Auto-Start on Match Launch**:
   - When launching into any map, the match directly starts with the Monster Hunt horror mode turned on by default (`mh_enabled 1`), rather than waiting for an explicit player toggle.
5. **Menu Complexity**:
   - The in-game `/horror` control menu contains a large number of configuration options, presets, debug toggles, and sub-menus, which can feel cluttered and overwhelming during fast-paced gameplay.
6. **Stuttery / Laggy Monster Movement**:
   - Because the monster is driven as a custom server-side entity utilizing waypoint-to-waypoint vector steps (`MOVETYPE_STEP` and manual velocity adjustments) rather than native player client physics, its movement and turning can appear stuttery or laggy in-game.
