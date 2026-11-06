# `de_raid` — Map Inspection & 2-Page Design Document (Steps 1 & 2)

## Part 1: Reference Check & Legal Isolation (Step 1)

### 1.1 Non-Use & Clean-Room Confirmation
- **Compiled Geometry (`mp_bo2raid3.ff` & `mp_bo2raid3_load.ff`)**: Confirmed in writing that the Call of Duty 4 FastFiles (`.ff` compiled geometry) **will NOT be loaded, decompiled, converted, or used**.
- **Archive Assets (`bo2raid3.iwd`)**: Confirmed in writing that **no** CoD4 / Activision textures (`.iwi`), models, scripts, or sounds from `bo2raid3.iwd` are extracted or copied. Only file/folder names inside the `.iwd` directory table were inspected to understand room themes.
- **Repository Safety**: `map/`, `*.iwd`, and `*.ff` are gitignored in `.gitignore`.

### 1.2 Reference Archive Summary (`map/mp_bo2raid3.1.zip`)
- **Files**: `bo2raid3.iwd` (`29.9 MB`, 313 entries), `mp_bo2raid3.ff` (`41.5 MB`), `mp_bo2raid3_load.ff` (`229 B`), `docs/Readme.txt` (`2,295 B`), `docs/mp_bo2raid3_checksums.md5` (`153 B`).
- **Author (`docs/Readme.txt`)**: **Hugo** (`hgbetatester@gmail.com`, `www.cod4dev.co.uk`, YouTube `UCux0A0hn4GhaMrHLaECcCaw`), v3.1 (`1 Jan 2018`) — CoD4 remake of Black Ops 2 `"Raid"`.
- **Zones Identified from Asset Names**: Driveway/Vista, Multi-Car Garage (`t6_civ_sportscar`, `bo2veh_luxury_sedan`, `garage_pipes`), Mansion Interior (`ind_stove` Kitchen, `furniture_couch3` Lounge, `art` Hall, `r_scan` Vault, Bedroom/Gym), Central Courtyard (`pillar_lower`, `statue_chinlion`), Pool & Jacuzzi Deck (`refwater`, `jacuzzi`, `chaise_lounge`), and Basketball Court (`setka`, `chain`, `"Now can play basket"`).

---

## Part 2: `de_raid` GoldSrc Bomb Defusal Design (Step 2)

### 2.1 Overview & Scale
- **Map Name**: `de_raid` (`czero/maps/de_raid.bsp`) — Bomb Defusal (`de_`).
- **Playable Bounds**: `3,328 x 3,968` GoldSrc units (`X: -1664..+1664`, `Y: -1984..+1984`, `Z: -64..+384`), tuned for 5v5 up to 12v12 Condition Zero matches with fast ~11–14 second rotations between Bombsites A and B.
- **Three-Lane Structure**:
  1. **West Lane (Close/Mid Rifles & SMGs)**: `Driveway (T)` -> `[Choke 1: Garage Bay]` -> **`Garage (Bombsite B)`** -> `Laundry` / `[Choke 2: Kitchen]` -> `Court (CT)`.
  2. **Center Lane (Mid Control & Flanks)**: `Driveway (T)` -> `Vault` / `Mansion Lounge` + elevated `Balcony` <-> **`Courtyard ("Ring")`** <-> `Patio Steps` -> `Court (CT)`.
  3. **East Lane (Long Sightlines & Water Deck)**: `Driveway (T)` -> `Garden` -> `Pool` + `[Choke 3: Cutout]` -> **`Gazebo (Bombsite A)`** -> `Court (CT)`.

### 2.2 Top-Down Layout Sketch (North = Top)

```text
                        NORTH (Y = +1984)
       +---------------------------------------------------+
       |            [ T SPAWN : DRIVEWAY / ENTRY ]         |
       |              (16 Spawns + T Buyzone)              |
       +---+-------------+---------------+-------------+---+
           |             |               |             |
           v             v               v             v
  +----------------+ +--------+     |         | +----------------+
  |   [CHOKE 1]    | | VAULT  |     |  NORTH  | |    GARDEN      |
  |  GARAGE DOORS  | | OFFICE |     |   ARCH  | |  (A Long Path) |
  +-------+--------+ +---+----+     +----+----+ +-------+--------+
  |                |     |               |              |        |
  |   [BOMBSITE B] |     |   MANSION     |              |  POOL  |
  |     GARAGE     +-----+   LOUNGE   [BALCONY]         | (Water |
  |  (2 Brush Cars |     |  & ART HALL   |              |  Deck) |
  |   for Cover)   |     +---+-------+---+              |        |
  |                |         |       |                  +---+----+
  +-------+--------+     +---+       |  COURTYARD       |   |    |
  |       |              |           |   ("RING")       |[CHOKE3]|
  |       |   [CHOKE 2]  |           |  [Lion Pedestal] | CUTOUT |
  |LAUNDRY+--- KITCHEN --+           |                  +---+----+
  | (West |   (Indoor    |           |                  |        |
  |  Hall)|    Choke)    |           |                  |[SITE A]|
  +---+---+--------------+-----------+------------------+ GAZEBO |
      |                         |                       | & DECK |
      v                         v                       +---+----+
  +---+-------------------------+---------------------------+----+
  |          [ CT SPAWN : BASKETBALL COURT & PATIO ]             |
  |        (16 Spawns + CT Buyzone + Decorative Hoop)            |
  +--------------------------------------------------------------+
                        SOUTH (Y = -1984)
```

### 2.3 GoldSrc Engine Limits & Brush Discipline
| Metric | GoldSrc Hard Limit | `de_raid` Target Budget | How We Stay Safe |
| :--- | ---: | ---: | :--- |
| `wpoly` (visible world polys) | `< 800` recommended | **`250 - 500`** (`> 100 FPS`) | Thick axial VIS-blocking walls between Mansion, Courtyard, Garage, and Pool; sky ceiling capped at `+384`. |
| `MAX_MAP_BRUSHES` / `PLANES` | `32,768` planes | **`< 3,500` planes** | Clean rectilinear brushwork; zero micro-carving or cylinder spam. |
| `MAX_MAP_CLIPNODES` | `32,767` | **`< 4,000` clipnodes** | Decorative trim, hoop backboard, pillars, and cars built as `func_wall` detail entities where appropriate. |
| `MAX_MAP_ENTITIES` | `1,024` (ZHLT: `4,096`) | **`~95` entities** | 32 spawns, 2 buyzones, 2 bomb targets, lights, `light_environment`, `info_map_parameters`, `ambient_generic`s, `func_water`, `func_wall` props. |
| Custom Textures (`de_raid.wad`) | 8-bit indexed, multiples of 16 (`<= 256x256`) | **Standard CS/CZ WADs + small original 8-bit `de_raid.wad`** | Uses `halflife.wad`, `cstrike.wad`, `cs_dust.wad`, `cs_office.wad`, `czde_sienna.wad`, plus original procedural 8-bit court/signage textures (`A`/`B`, court lines, pool tile). |

### 2.4 Bot Navigation & Pathing Rules (Step 3 & Step 5 Readiness)
- **Zero Ladders & Zero Crouch-Only Tunnels**: Every connector is walkable upright (`width >= 112`, `height >= 128`).
- **Bot-Friendly Stairs & Pool**: All stairs use `8`-unit step height (`16`-unit depth) so Condition Zero's `bot_nav_analyze` builds a single connected navmesh with zero stuck spots. The swimming pool (`Pool`) is `40` units deep with broad full-width walk-out steps on both North and South ends so bots never drown or get trapped in water.
- **Decorative Basketball Hoop (`Court`)**: Built cleanly from 4 simple `func_wall` brushes (post, backboard with original 8-bit target square texture, and rim) at the south edge of CT Spawn — out of the main rush path so bots never snag on it.

### 2.5 Area Callouts Saved to `maps/de_raid_callouts.json`
14 named callouts saved for AI Teammates integration:
`Driveway` (T Spawn), `Court` (CT Spawn), `Garage` (Site B), `Laundry`, `Kitchen`, `Mansion`, `Vault`, `Balcony`, `Courtyard` (`Ring`), `Cutout`, `Garden`, `Pool`, `Gazebo` (Site A), and `Patio Steps`.
