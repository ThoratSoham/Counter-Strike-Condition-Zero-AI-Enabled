import os
import json
import time

class MemoryManager:
    """
    Persists long-term player relationships, match history, and memorable moments.
    """
    def __init__(self, memory_file=None):
        if memory_file is None:
            memory_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.json")
        self.memory_file = memory_file
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "matches_played": 0,
            "matches_won": 0,
            "player_carries": 0,
            "player_clutches": 0,
            "friendly_fire_incidents": 0,
            "last_match_date": None,
            "notable_moments": []
        }

    def save(self):
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"[MemoryManager] Error saving memory: {e}")

    def record_match_end(self, won: bool):
        self.data["matches_played"] += 1
        if won:
            self.data["matches_won"] += 1
        self.data["last_match_date"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self.save()

    def record_clutch(self):
        self.data["player_clutches"] += 1
        self.save()

    def record_friendly_fire(self):
        self.data["friendly_fire_incidents"] += 1
        self.save()

    def add_moment(self, description: str):
        self.data["notable_moments"].append({
            "time": time.strftime("%Y-%m-%d %H:%M"),
            "description": description
        })
        if len(self.data["notable_moments"]) > 20:
            self.data["notable_moments"].pop(0)
        self.save()

    def get_summary(self) -> str:
        return (
            f"Matches: {self.data['matches_played']} (Won: {self.data['matches_won']}), "
            f"Player Clutches: {self.data['player_clutches']}, "
            f"Friendly Fires: {self.data['friendly_fire_incidents']}"
        )
