"""
Mouse Unlock - Setup Script
Run this once to register your secret click pattern.
"""

import json
import hashlib
import threading
import time
import sys
from pathlib import Path
from pynput import mouse

CONFIG_FILE = Path("config.json")


def hash_pattern(clicks: list[str]) -> str:
    return hashlib.sha256(",".join(clicks).encode()).hexdigest()


def record_pattern(label: str) -> list[str]:
    clicks = []
    stop_event = threading.Event()

    def on_click(x, y, button, pressed):
        if pressed and not stop_event.is_set():
            if button == mouse.Button.left:
                clicks.append("L")
                symbol = "◀ LEFT"
            elif button == mouse.Button.right:
                clicks.append("R")
                symbol = "▶ RIGHT"
            else:
                return  # ignore middle click
            print(f"  {symbol}   →  [{' · '.join(clicks)}]")

    print(f"\n{label}")
    print("  Left click = L   |   Right click = R")
    input("  Press ENTER when ready to start recording...\n")
    print("  Go! Click your pattern, then press ENTER to stop.\n")

    # Wait for Enter in a separate thread
    def wait_enter():
        input()
        stop_event.set()

    t = threading.Thread(target=wait_enter, daemon=True)
    t.start()

    with mouse.Listener(on_click=on_click) as listener:
        stop_event.wait()
        listener.stop()

    return clicks


def choose_hotkey() -> str:
    print("\n  Choose a lock hotkey:")
    options = {
        "1": "<ctrl>+<alt>+l",
        "2": "<ctrl>+<shift>+l",
        "3": "<ctrl>+<alt>+z",
        "4": "<ctrl>+<alt>+x",
    }
    labels = {
        "1": "Ctrl + Alt + L  (default)",
        "2": "Ctrl + Shift + L",
        "3": "Ctrl + Alt + Z",
        "4": "Ctrl + Alt + X",
    }
    for k, v in labels.items():
        print(f"    {k}. {v}")

    choice = input("\n  Enter choice [1]: ").strip() or "1"
    return options.get(choice, options["1"])


def main():
    print("=" * 52)
    print("   Mouse Unlock -- Pattern Setup")
    print("=" * 52)

    if CONFIG_FILE.exists():
        ans = input("\nA config already exists. Overwrite? (y/n): ").strip().lower()
        if ans != "y":
            print("Setup cancelled.")
            sys.exit(0)

    while True:
        # Step 1: Record
        pattern1 = record_pattern("STEP 1 -- Click your secret pattern:")

        if len(pattern1) < 2:
            print("\n  ✗  Pattern needs at least 2 clicks. Try again.")
            continue

        print(f"\n  Pattern recorded: [{' · '.join(pattern1)}] ({len(pattern1)} clicks)")

        # Step 2: Confirm
        pattern2 = record_pattern("STEP 2 -- Repeat the same pattern to confirm:")

        if pattern1 == pattern2:
            print(f"\n  ✓  Patterns match!")
            break
        else:
            print(f"\n  ✗  Patterns don't match.")
            print(f"     First:   [{' · '.join(pattern1)}]")
            print(f"     Second:  [{' · '.join(pattern2)}]")
            retry = input("  Try again? (y/n): ").strip().lower()
            if retry != "y":
                print("Setup cancelled.")
                sys.exit(0)

    hotkey = choose_hotkey()
    hotkey_display = hotkey.replace("<", "").replace(">", "").replace("+", " + ").upper()

    config = {
        "pattern_hash": hash_pattern(pattern1),
        "pattern_length": len(pattern1),
        "hotkey": hotkey,
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\n  Config saved → {CONFIG_FILE}")
    print(f"  Lock hotkey  → {hotkey_display}")
    print(f"  Pattern      → {len(pattern1)} clicks (stored as hash, never plaintext)")
    print("\n  Run  python mouse_unlock.py  to start!\n")


if __name__ == "__main__":
    main()
