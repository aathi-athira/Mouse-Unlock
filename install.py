"""
Mouse Unlock -- Install
Registers mouse_unlock.py to run silently on Windows login via Task Scheduler.
Run once: python install.py
"""

import subprocess
import sys
from pathlib import Path

TASK_NAME = "MouseUnlock"


def get_paths():
    python = sys.executable
    script = str(Path(__file__).parent.resolve() / "mouse_unlock.py")
    return python, script


def install():
    python, script = get_paths()

    print(f"Installing MouseUnlock as a startup task...")
    print(f"  Python : {python}")
    print(f"  Script : {script}")

    # Build the schtasks command
    cmd = [
        "schtasks", "/create",
        "/tn", TASK_NAME,
        "/tr", f'"{python}" "{script}"',
        "/sc", "ONLOGON",
        "/rl", "HIGHEST",
        "/f",   # overwrite if exists
        "/it",  # only when user is logged in
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"\n  SUCCESS -- MouseUnlock will now start automatically on login.")
        print(f"  To disable : open Task Scheduler and disable '{TASK_NAME}'")
        print(f"  To remove  : run  python uninstall.py")
        print(f"\n  Starting it now...")
        subprocess.Popen([python, script])
        print(f"  MouseUnlock is running. Press Ctrl+Alt+L to lock.")
    else:
        print(f"\n  ERROR -- Task Scheduler returned:")
        print(f"  {result.stderr or result.stdout}")
        print(f"\n  Try running this script as Administrator.")


if __name__ == "__main__":
    install()
