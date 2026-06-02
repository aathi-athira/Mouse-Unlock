"""
Mouse Unlock -- Main App
Runs in the background. Press your hotkey to show the lock screen.
Unlock by clicking your registered secret pattern.
"""

import json
import hashlib
import sys
import queue
import threading
from pathlib import Path
from datetime import datetime
import tkinter as tk
from pynput import keyboard

CONFIG_FILE = Path("config.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_config() -> dict:
    if not CONFIG_FILE.exists():
        print("[ERROR] config.json not found -- run setup.py first.")
        sys.exit(1)
    with open(CONFIG_FILE) as f:
        cfg = json.load(f)
    if not cfg.get("pattern_hash"):
        print("[ERROR] No pattern in config -- run setup.py first.")
        sys.exit(1)
    return cfg


def hash_clicks(clicks: list[str]) -> str:
    return hashlib.sha256(",".join(clicks).encode()).hexdigest()


# ---------------------------------------------------------------------------
# Lock Screen
# ---------------------------------------------------------------------------

class LockScreen:
    """Fullscreen tkinter overlay -- unlocked by the correct click pattern."""

    # Visual states
    _COLOR_BG        = "#0d0d0d"
    _COLOR_TIME      = "#ffffff"
    _COLOR_DATE      = "#666666"
    _COLOR_HINT      = "#444444"
    _COLOR_DOTS_IDLE = "#3a7bd5"
    _COLOR_OK        = "#2ecc71"
    _COLOR_ERR       = "#e74c3c"

    def __init__(self, pattern_hash: str, pattern_length: int):
        self.pattern_hash   = pattern_hash
        self.pattern_length = pattern_length
        self.clicks: list[str] = []
        self._timeout_id    = None

        self.root = tk.Tk()
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        r = self.root
        r.attributes("-fullscreen", True)
        r.attributes("-topmost", True)
        r.overrideredirect(True)
        r.configure(bg=self._COLOR_BG)

        # Block Alt+F4 / close button
        r.protocol("WM_DELETE_WINDOW", lambda: None)

        center = tk.Frame(r, bg=self._COLOR_BG)
        center.place(relx=0.5, rely=0.45, anchor="center")

        # Lock icon
        tk.Label(center, text="[LOCKED]", font=("Segoe UI", 16),
                 bg=self._COLOR_BG, fg="#555555").pack(pady=(0, 16))

        # Clock
        self._lbl_time = tk.Label(center, font=("Segoe UI Light", 72),
                                   bg=self._COLOR_BG, fg=self._COLOR_TIME)
        self._lbl_time.pack()

        # Date
        self._lbl_date = tk.Label(center, font=("Segoe UI", 18),
                                   bg=self._COLOR_BG, fg=self._COLOR_DATE)
        self._lbl_date.pack(pady=(4, 32))

        # Dot indicators (one per click)
        self._lbl_dots = tk.Label(center, text="",
                                   font=("Segoe UI", 22),
                                   bg=self._COLOR_BG, fg=self._COLOR_DOTS_IDLE)
        self._lbl_dots.pack(pady=4)

        # Status line
        self._lbl_status = tk.Label(center,
                                     text="click your secret pattern to unlock",
                                     font=("Segoe UI", 13),
                                     bg=self._COLOR_BG, fg=self._COLOR_HINT)
        self._lbl_status.pack(pady=(6, 0))

        # Bind left and right clicks
        r.bind("<Button-1>", lambda _: self._on_click("L"))
        r.bind("<Button-3>", lambda _: self._on_click("R"))

        # Steal focus so Alt+Tab is swallowed
        r.focus_force()
        r.grab_set()

        self._tick()

    def _tick(self):
        now = datetime.now()
        self._lbl_time.config(text=now.strftime("%H:%M"))
        self._lbl_date.config(text=now.strftime("%A, %B %d"))
        self.root.after(1000, self._tick)

    # ------------------------------------------------------------------
    # Pattern logic
    # ------------------------------------------------------------------

    def _on_click(self, btn: str):
        self.clicks.append(btn)
        n = len(self.clicks)
        self._lbl_dots.config(text="  ".join(["●"] * n), fg=self._COLOR_DOTS_IDLE)

        # Cancel any pending auto-check
        if self._timeout_id:
            self.root.after_cancel(self._timeout_id)
            self._timeout_id = None

        if n == self.pattern_length:
            # Exact length -- check immediately
            self._check()
        elif n > self.pattern_length:
            # Too many clicks -- always wrong, reset
            self._wrong()
        else:
            # Still building up -- schedule a timeout so a short pattern
            # entered slowly still triggers a check
            self._timeout_id = self.root.after(3000, self._check)

    def _check(self):
        if hash_clicks(self.clicks) == self.pattern_hash:
            self._unlock()
        else:
            self._wrong()

    def _unlock(self):
        self._lbl_dots.config(text="✓", fg=self._COLOR_OK)
        self._lbl_status.config(text="unlocked", fg=self._COLOR_OK)
        self.root.after(380, self._close)

    def _wrong(self):
        self._lbl_dots.config(text="✗", fg=self._COLOR_ERR)
        self._lbl_status.config(text="incorrect pattern -- try again", fg=self._COLOR_ERR)
        self.clicks = []
        self.root.after(1100, self._reset_ui)

    def _reset_ui(self):
        self._lbl_dots.config(text="", fg=self._COLOR_DOTS_IDLE)
        self._lbl_status.config(text="click your secret pattern to unlock",
                                  fg=self._COLOR_HINT)

    def _close(self):
        self.root.grab_release()
        self.root.destroy()

    # ------------------------------------------------------------------

    def show(self):
        """Block until unlocked (or window destroyed)."""
        self.root.mainloop()


# ---------------------------------------------------------------------------
# Hotkey listener (background thread)
# ---------------------------------------------------------------------------

class HotkeyListener:
    def __init__(self, hotkey: str, q: queue.Queue):
        self._hotkey = hotkey
        self._q = q

    def start(self):
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def _run(self):
        try:
            with keyboard.GlobalHotKeys({self._hotkey: self._fire}) as h:
                h.join()
        except Exception as exc:
            print(f"[HOTKEY] Listener error: {exc}")

    def _fire(self):
        self._q.put("LOCK")


# ---------------------------------------------------------------------------
# Main app loop
# ---------------------------------------------------------------------------

def main():
    cfg = load_config()
    hotkey        = cfg["hotkey"]
    pattern_hash  = cfg["pattern_hash"]
    pattern_len   = cfg["pattern_length"]

    hotkey_display = (hotkey.replace("<", "")
                            .replace(">", "")
                            .replace("+", " + ")
                            .upper())

    print("=" * 46)
    print("   Mouse Unlock -- running")
    print("=" * 46)
    print(f"   Lock hotkey : {hotkey_display}")
    print(f"   Pattern     : {pattern_len} clicks (L / R)")
    print(f"   Stop        : Ctrl + C")
    print()

    q: queue.Queue = queue.Queue()
    locked = threading.Event()   # prevent stacking lock screens

    HotkeyListener(hotkey, q).start()

    try:
        while True:
            try:
                msg = q.get(timeout=0.5)
            except queue.Empty:
                continue

            if msg == "LOCK" and not locked.is_set():
                locked.set()
                print("[APP] Locked -- enter pattern to unlock.")
                screen = LockScreen(pattern_hash, pattern_len)
                screen.show()
                print("[APP] Unlocked.")
                locked.clear()

    except KeyboardInterrupt:
        print("\n[APP] Stopped.")


if __name__ == "__main__":
    main()
