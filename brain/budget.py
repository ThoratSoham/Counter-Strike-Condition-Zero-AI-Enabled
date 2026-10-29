import time

class TalkBudgetManager:
    """
    Monitors daily free-tier API usage to guarantee zero unexpected costs.
    Displays 'AI Energy' bar and shifts to pre-generated Voice Line Library when budget runs low.
    """
    def __init__(self, daily_limit: int = 500):
        self.daily_limit = daily_limit
        self.requests_today = 0
        self.current_day = time.strftime("%Y-%m-%d")

    def _check_day_rollover(self):
        today = time.strftime("%Y-%m-%d")
        if today != self.current_day:
            self.current_day = today
            self.requests_today = 0

    def record_request(self):
        self._check_day_rollover()
        self.requests_today += 1

    def can_make_cloud_request(self) -> bool:
        self._check_day_rollover()
        return self.requests_today < self.daily_limit

    def get_energy_percentage(self) -> int:
        self._check_day_rollover()
        remaining = max(0, self.daily_limit - self.requests_today)
        return int((remaining / self.daily_limit) * 100)

    def get_stats(self) -> dict:
        self._check_day_rollover()
        return {
            "used": self.requests_today,
            "limit": self.daily_limit,
            "remaining": max(0, self.daily_limit - self.requests_today),
            "energy_pct": self.get_energy_percentage()
        }
