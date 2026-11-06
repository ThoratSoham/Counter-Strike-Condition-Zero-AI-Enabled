"""
Map Callout Loader & Tactical Area Name Engine (Step 6).
Loads custom map callout definitions from `maps/<map_name>_callouts.json`
(e.g. `maps/de_raid_callouts.json`) so AI Teammates use authentic map area
names ("Pool", "Garage", "Court", "Mansion", "Courtyard", "Ring", "Kitchen",
"Balcony", "Gazebo", "Cutout", "Vault", "Laundry") in both LLM and local chat.
"""

from __future__ import annotations

import json
import os
import random
from typing import Dict, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS_DIR = os.path.join(BASE_DIR, "maps")

_CALLOUT_CACHE: Dict[str, Optional[dict]] = {}


def load_map_callouts(map_name: str) -> Optional[dict]:
    """Load `maps/<map_name>_callouts.json` if present (cached)."""
    norm = (map_name or "").strip().lower()
    if norm.endswith(".bsp"):
        norm = norm[:-4]
    if not norm:
        return None
    if norm in _CALLOUT_CACHE:
        return _CALLOUT_CACHE[norm]

    json_path = os.path.join(MAPS_DIR, f"{norm}_callouts.json")
    if not os.path.exists(json_path):
        _CALLOUT_CACHE[norm] = None
        return None

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _CALLOUT_CACHE[norm] = data
        return data
    except Exception:
        _CALLOUT_CACHE[norm] = None
        return None


def get_callout_names(map_name: str) -> List[str]:
    data = load_map_callouts(map_name)
    if not data:
        return []
    return [c.get("name", "") for c in data.get("callouts", []) if c.get("name")]


def get_callout_at_xyz(map_name: str, x: float, y: float, z: float) -> Optional[str]:
    """Return the matching callout name for 3D GoldSrc world coordinates (x, y, z)."""
    data = load_map_callouts(map_name)
    if not data:
        return None
    for c in data.get("callouts", []):
        b = c.get("bounds") or {}
        bmin = b.get("min")
        bmax = b.get("max")
        if bmin and bmax and len(bmin) == 3 and len(bmax) == 3:
            if bmin[0] <= x <= bmax[0] and bmin[1] <= y <= bmax[1] and bmin[2] <= z <= bmax[2]:
                return c.get("name")
    return None


def build_llm_callout_section(map_name: str) -> str:
    """Build a prompt section instructing the LLM to use exact area names from `<map>_callouts.json`."""
    data = load_map_callouts(map_name)
    if not data:
        return ""
    callouts = data.get("callouts", [])
    if not callouts:
        return ""

    entries = []
    sites = []
    for c in callouts:
        name = c.get("name", "")
        aliases = c.get("aliases", [])
        site = c.get("is_bombsite")
        alias_str = f" (also called: {', '.join(aliases[:2])})" if aliases else ""
        if site:
            sites.append(f"Bombsite {site} = {name}{alias_str}")
        entries.append(f"{name}{alias_str}")

    return (
        f"\nMAP AREA CALLOUTS FOR {data.get('display_name', map_name)} ({map_name}):\n"
        f"- Bombsites: {'; '.join(sites) if sites else 'Standard A and B'}\n"
        f"- Named Areas: {', '.join(entries)}\n"
        "- IMPORTANT: Naturally reference these exact map callout names (e.g. Pool, Garage, Court, Mansion, Courtyard/Ring, Kitchen, Balcony, Gazebo, Cutout) in at least half of your tactical banter and callouts!\n"
    )


# Multi-turn local scripts tailored to de_raid_callouts.json when running offline or saving quota
DE_RAID_CONVERSATIONS = [
    [
        ("Vikram", "Full send through Garage! Clear the sports cars and plant B!", "hype", "aggressive"),
        ("Kabir", "Last time I pushed Garage I hid behind the red car and still got tapped.", "laugh", "amused"),
        ("Marcus", "I'll hold Courtyard and Balcony. Watch Cutout flank.", "", "calm"),
        ("Sunny", "Wait is Bombsite A at Gazebo by the Pool?! Don't leave me alone!", "shock", "nervous"),
    ],
    [
        ("Sunny", "Guys can I go swim in the Pool for five seconds?", "", "nervous"),
        ("Vikram", "NO SWIMMING AT POOL! Hold Gazebo or watch Cutout window!", "shut_up", "annoyed"),
        ("Kabir", "Sunny brought floaties to Bombsite A lmaooo", "laugh", "amused"),
        ("Marcus", "Focus. Footsteps near Kitchen and Laundry.", "", "calm"),
    ],
    [
        ("Kabir", "Bro I tried a fadeaway jumper at Court in spawn, bricked it hard.", "laugh", "amused"),
        ("Vikram", "Stop playing basketball at Court and rotate through Mansion!", "roast", "aggressive"),
        ("Marcus", "One crossing Courtyard Ring by the lion statue.", "", "calm"),
        ("Sunny", "I'm watching Vault and Driveway, nobody's flanking yet!", "", "nervous"),
    ],
    [
        ("Marcus", "Sniper holding Courtyard from Balcony stairs. Smoke Mid.", "", "calm"),
        ("Vikram", "Forget Mid, let's breach Kitchen from Laundry and take Garage!", "hype", "aggressive"),
        ("Sunny", "Okay I'm watching Mansion paintings hall... those frames look expensive.", "", "nervous"),
        ("Kabir", "Don't shoot the Mansion art Sunny, it costs more than your loadout!", "roast", "amused"),
    ],
    [
        ("Vikram", "Push Garden onto Pool deck! Take Gazebo for an easy A plant!", "hype", "aggressive"),
        ("Marcus", "Careful at Cutout choke, CTs always crossfire Pool from Court.", "", "calm"),
        ("Kabir", "If I die on Patio Steps, bury me next to the Basketball Court hoop.", "laugh", "amused"),
    ],
]

DE_RAID_EVENT_CALLOUTS: Dict[str, List[Tuple[str, Optional[str]]]] = {
    "round_start": [
        ("Raid time! Watch Courtyard Ring, Garage cars, and Pool deck!", "greeting"),
        ("New round on de_raid! Split Mansion and Pool toward Gazebo A!", "hype"),
        ("Leave the basketball hoop at Court alone and hold Kitchen & Garage!", "greeting"),
    ],
    "bomb_planted": [
        ("BOMB IS DOWN! Check Gazebo at Pool deck and Garage behind the cars!", "shock"),
        ("Bomb planted! Lock down Cutout, Kitchen, and Courtyard Ring!", "hype"),
    ],
    "bomb_defused": [
        ("Defuse secured! Mansion and Pool deck are clean, huge hold!", "hype"),
        ("Clutch defuse! Send them right back up Driveway!", "praise"),
    ],
    "kill": [
        ("Dropped him clean in Courtyard Ring! Push Mansion!", "kill_headshot"),
        ("Folded that guy by Pool deck! Gazebo Site A is wide open!", "hype"),
        ("Deleted him between the Garage cars! Site B is ours!", "kill_headshot"),
        ("Picked one off Balcony stairs! Keep moving!", "praise"),
    ],
    "death": [
        ("He's camping behind the sports car in Garage! Trade me!", "fail_sad"),
        ("Tagged him in Kitchen near Laundry door, he's one shot!", "shock"),
        ("Careful, someone's holding Pool deck from Cutout!", "fail_sad"),
        ("Caught me crossing Courtyard from Patio Steps, watch Balcony!", "fail_sad"),
    ],
}


def generate_map_idle_batch(map_name: str, size: int = 8, clean_mode: bool = False) -> List[dict]:
    """Return multi-turn idle banter lines referencing real callouts from `maps/<map>_callouts.json`."""
    data = load_map_callouts(map_name)
    if not data:
        return []

    norm = (map_name or "").strip().lower()
    out: List[dict] = []
    if norm == "de_raid":
        groups = list(DE_RAID_CONVERSATIONS)
        random.shuffle(groups)
        for grp in groups:
            for speaker, text, tag, mood in grp:
                out.append(
                    {
                        "speaker": speaker,
                        "text": text,
                        "sound_tag": tag or "",
                        "delay_ms": random.randint(1350, 2100),
                        "mood": mood,
                    }
                )
            if len(out) >= size:
                break
        return out[:size]

    # Generic support for any future custom `<map>_callouts.json`
    names = get_callout_names(map_name)
    if len(names) >= 2:
        a, b = random.sample(names, 2)
        out.append({"speaker": "Marcus", "text": f"Check {a}, then rotate toward {b}.", "sound_tag": "", "delay_ms": 1500, "mood": "calm"})
        out.append({"speaker": "Vikram", "text": f"Pushing {a} right now, back me up!", "sound_tag": "hype", "delay_ms": 1600, "mood": "aggressive"})
    return out


def maybe_pick_map_event_line(map_name: str, event_type: str) -> Optional[Tuple[str, Optional[str]]]:
    """Return a map-aware callout reaction for de_raid (~65% of events so callouts feel natural and varied)."""
    norm = (map_name or "").strip().lower()
    if norm != "de_raid":
        return None
    pool = DE_RAID_EVENT_CALLOUTS.get(event_type)
    if not pool:
        return None
    if event_type in ("round_start", "bomb_planted", "bomb_defused") or random.random() < 0.65:
        return random.choice(pool)
    return None


def build_map_direct_reply(map_name: str, message: str, speaker: str, sender: str = "Player") -> Optional[Tuple[str, str]]:
    """
    When a human player asks about positions/sites/callouts on `de_raid` (and LLM is offline),
    answer directly using the real area names from `maps/de_raid_callouts.json`.
    """
    data = load_map_callouts(map_name)
    if not data:
        return None

    msg_l = (message or "").lower()
    prefix = f"{sender}, " if sender and sender.lower() not in ("player", "server") else ""

    # Check if player mentioned any callout or alias from de_raid_callouts.json
    for c in data.get("callouts", []):
        cname = c.get("name", "")
        terms = [cname.lower()] + [a.lower() for a in c.get("aliases", [])]
        if any(t and t in msg_l for t in terms):
            site = c.get("is_bombsite")
            if site:
                return (
                    f"{prefix}copy that, rotating to {cname} (Bombsite {site}) right now!",
                    "hype",
                )
            return (
                f"{prefix}on my way to {cname}, watch the crossfire from Courtyard!",
                "hype",
            )

    if any(k in msg_l for k in ("where", "callout", "site", "rush", "help", "plan", "push", "rotate")):
        names = get_callout_names(map_name)
        if names:
            pick_a = "Garage" if "Garage" in names else names[0]
            pick_b = "Pool" if "Pool" in names else names[-1]
            pick_c = "Mansion" if "Mansion" in names else names[len(names) // 2]
            return (
                f"{prefix}push {pick_c} and {pick_b} toward Gazebo A, or hit {pick_a} for B!",
                "hype",
            )
    return None

