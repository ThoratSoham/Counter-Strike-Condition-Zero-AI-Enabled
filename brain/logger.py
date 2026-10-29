import os
import time

class ModLogger:
    """
    Unified logger for AI Teammates mod, writing to logs/mod.log and console.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ModLogger, cls).__new__(cls)
            cls._instance._init_logger()
        return cls._instance

    def _init_logger(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.logs_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        self.log_file = os.path.join(self.logs_dir, "mod.log")

    def log(self, step: int, message: str):
        """
        Log a specific mod pipeline step:
        1: Plugin loaded
        2: Game event sent
        3: Brain received event
        4: AI API called
        5: AI answer received / error
        6: Chat message sent into game as bot
        7: Sound played
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        prefix = f"[Step {step}]" if step > 0 else "[Info]"
        formatted = f"[{timestamp}] {prefix} {message}"
        print(formatted)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")
        except Exception as e:
            print(f"Failed to write log: {e}")

    def log_offline(self, reason: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] [AI] offline: {reason}"
        print(formatted)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")
        except Exception:
            pass

def get_logger():
    return ModLogger()
