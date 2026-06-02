"""
Mouse Unlock -- Uninstall
Removes the MouseUnlock startup task and kills any running instance.
Run: python uninstall.py
"""

import subprocess
import sys

TASK_NAME = "MouseUnlock"


def uninstall():
    print("Removing MouseUnlock...")

    # Kill any running instance
    subprocess.run(
        ["taskkill", "/f", "/fi", f"WINDOWTITLE eq {TASK_NAME}"],
        capture_output=True
    )
    # Kill by script name just in case
    subprocess.run(
        ["taskkill", "/f", "/fi", "IMAGENAME eq python.exe",
         "/fi", "WINDOWTITLE eq mouse_unlock*"],
        capture_output=True
    )

    # Remove the scheduled task
    result = subprocess.run(
        ["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        print(f"  SUCCESS -- '{TASK_NAME}' startup task removed.")
        print(f"  MouseUnlock will no longer start on login.")
    else:
        err = result.stderr or result.stdout
        if "cannot find" in err.lower() or "not exist" in err.lower():
            print(f"  Task '{TASK_NAME}' was not installed.")
        else:
            print(f"  ERROR: {err.strip()}")
            print(f"  Try running as Administrator.")


if __name__ == "__main__":
    uninstall()
