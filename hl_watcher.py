import os
import time
import subprocess
from brain.service import is_hl_process_running
from main import is_brain_already_running

def run_watcher():
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    print("[Watcher] Watching for hl.exe (Condition Zero) to auto-start AI Brain Service...")
    brain_proc = None

    while True:
        try:
            hl_running = is_hl_process_running()
            if hl_running:
                if (brain_proc is None or brain_proc.poll() is not None) and not is_brain_already_running():
                    print("[Watcher] Detected hl.exe running! Starting AI Brain Service (main.py --no-ui)...")
                    brain_proc = subprocess.Popen(
                        ["py", "main.py", "--no-ui"],
                        cwd=project_root
                    )
            else:
                if brain_proc is not None and brain_proc.poll() is not None:
                    brain_proc = None
        except Exception as e:
            print(f"[Watcher] Error: {e}")
        time.sleep(1.5)

if __name__ == "__main__":
    run_watcher()

