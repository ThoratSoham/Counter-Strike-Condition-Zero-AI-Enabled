class MoodManager:
    """
    Manages emotional meters (happiness, confidence, stress, tilt) for each teammate.
    Meters range from 0 to 100 and evolve dynamically with game events.
    """
    def __init__(self, personalities: dict):
        self.personalities = personalities
        self.moods = {}
        self.reset_all()

    def reset_all(self):
        for t_id, data in self.personalities.items():
            defaults = data.get("mood_defaults", {})
            self.moods[t_id] = {
                "happiness": defaults.get("happiness", 50),
                "confidence": defaults.get("confidence", 50),
                "stress": defaults.get("stress", 20),
                "tilt": defaults.get("tilt", 10)
            }

    def get_mood(self, t_id: str) -> dict:
        m = self.moods.get(t_id, {"happiness": 50, "confidence": 50, "stress": 20, "tilt": 10})
        return dict(m)

    def update_on_kill(self, killer_id: str, is_headshot: bool = False):
        if killer_id in self.moods:
            m = self.moods[killer_id]
            m["happiness"] = min(100, m["happiness"] + (15 if is_headshot else 10))
            m["confidence"] = min(100, m["confidence"] + 15)
            m["tilt"] = max(0, m["tilt"] - 15)
            m["stress"] = max(0, m["stress"] - 10)

        # Team gets morale boost
        for t_id, m in self.moods.items():
            if t_id != killer_id:
                m["confidence"] = min(100, m["confidence"] + 5)
                m["stress"] = max(0, m["stress"] - 5)

    def update_on_death(self, victim_id: str, is_headshot: bool = False, is_camper: bool = False):
        if victim_id in self.moods:
            m = self.moods[victim_id]
            # Vikram tilts harder on death
            tilt_inc = 25 if victim_id == "vikram" else 15
            if is_camper:
                tilt_inc += 15
            m["tilt"] = min(100, m["tilt"] + tilt_inc)
            m["happiness"] = max(0, m["happiness"] - 15)
            m["stress"] = min(100, m["stress"] + 15)
            m["confidence"] = max(10, m["confidence"] - 10)

    def update_on_round_win(self, close_round: bool = False):
        for t_id, m in self.moods.items():
            m["happiness"] = min(100, m["happiness"] + 20)
            m["confidence"] = min(100, m["confidence"] + 15)
            m["tilt"] = max(0, m["tilt"] - 25)
            m["stress"] = max(0, m["stress"] - 20)

    def update_on_round_loss(self, loss_streak: int = 1):
        for t_id, m in self.moods.items():
            m["happiness"] = max(0, m["happiness"] - 15)
            m["stress"] = min(100, m["stress"] + (10 * loss_streak))
            # Hothead tilts faster
            mult = 1.5 if t_id == "vikram" else 1.0
            m["tilt"] = min(100, m["tilt"] + int(12 * loss_streak * mult))

    def update_on_friendly_fire(self, victim_id: str):
        if victim_id in self.moods:
            m = self.moods[victim_id]
            m["tilt"] = min(100, m["tilt"] + 20)
            m["happiness"] = max(0, m["happiness"] - 10)

    def is_tilted(self, t_id: str) -> bool:
        return self.moods.get(t_id, {}).get("tilt", 0) > 65
