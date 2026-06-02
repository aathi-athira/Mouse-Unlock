# Mouse Unlock — Windows Edition

Unlock your screen with a secret mouse-click pattern instead of typing a password.
Inspired by a Linux project that used `loginctl unlock-sessions` with `evdev`.
This is the Windows equivalent — built from scratch in Python.

---

## What It Does

- Runs silently in the background after login
- Press a hotkey (e.g. `Ctrl+Alt+L`) to show a fullscreen black lock screen
- Click your secret pattern (sequence of left/right clicks) to unlock
- Wrong pattern shows an error and resets — try again
- Your pattern is **never stored in plaintext** — only a SHA256 hash is saved

---

## How We Built It

### Inspiration
The original project was a ~150-line Python script for Linux that:
- Read raw mouse input from `/dev/input/` using `evdev`
- Monitored session lock via `loginctl`
- Ran as a `systemd` service

### Windows Challenges
Windows has no `loginctl`, no `/dev/input/`, and no direct way to unlock the actual Windows lock screen programmatically. So we took a different approach:

- **Custom fullscreen overlay** (tkinter) acts as the lock screen instead of the OS lock screen
- **`pynput`** replaces `evdev` for mouse and keyboard input on Windows
- **Task Scheduler** replaces `systemd` for auto-starting on login
- **Queue-based threading** — hotkey listener runs on a background thread, tkinter UI runs on the main thread, they communicate via a `queue.Queue`

### Security Design
- Pattern is hashed with SHA256 before saving — the actual click sequence is never stored
- Pattern length is stored (not the pattern itself) so the lock screen knows when to evaluate
- `config.json` contains only: `pattern_hash`, `pattern_length`, `hotkey`

---

## Project Structure

```
MouseUnlock/
  setup.py          — Register your secret click pattern (run once)
  mouse_unlock.py   — Main app: runs in background, shows lock screen on hotkey
  install.py        — Register mouse_unlock.py to auto-start on Windows login
  uninstall.py      — Remove the auto-start task
  config.json       — Auto-generated: stores pattern hash + hotkey (never the pattern)
  requirements.txt  — Python dependencies
```

---

## Requirements

- Python 3.10+
- Windows 10 or 11

---

## Setup & Installation

### Step 1 — Install dependencies

Open PowerShell or CMD and navigate to the project folder:

```
cd <path-to-MouseUnlock-folder>
pip install -r requirements.txt
```

Only one dependency: `pynput`

---

### Step 2 — Register your pattern

```
python <path-to-MouseUnlock-folder>\setup.py
```

Follow the prompts:
1. Press `Enter` to start recording
2. Click your secret pattern using left and right mouse buttons (minimum 2 clicks)
3. Press `Enter` to stop
4. Repeat the same pattern to confirm
5. Choose a lock hotkey:
   - `1` — Ctrl + Alt + L *(default)*
   - `2` — Ctrl + Shift + L
   - `3` — Ctrl + Alt + Z
   - `4` — Ctrl + Alt + X

This saves `config.json` with the hashed pattern. The actual click sequence is discarded.

---

### Step 3 — Test it manually

```
python <path-to-MouseUnlock-folder>\mouse_unlock.py
```

- The app starts and waits in the background (terminal stays open)
- Press your hotkey → fullscreen lock screen appears
- Click your pattern → screen unlocks
- Press `Ctrl+C` in the terminal to stop

---

### Step 4 — Install to auto-start on login

```
python <path-to-MouseUnlock-folder>\install.py
```

This registers a **Windows Task Scheduler** task named `MouseUnlock` that:
- Launches silently (no terminal window) on every login
- Runs with your user permissions
- Also starts the app immediately so you don't need to reboot

From this point on, Mouse Unlock is always running in the background after login.

---

## Daily Usage

| Action | How |
|--------|-----|
| Lock screen | Press `Ctrl+Alt+L` (or your chosen hotkey) |
| Unlock | Click your secret pattern on the black screen |
| Wrong pattern | Shows `✗` — clicks reset automatically, try again |

---

## Managing the App

### Temporarily disable (keep installed)
1. Open **Task Scheduler** (search in Start Menu)
2. Find `MouseUnlock` in the task list
3. Right-click → **Disable**
4. To re-enable: right-click → **Enable**

### Uninstall completely

```
python <path-to-MouseUnlock-folder>\uninstall.py
```

This removes the Task Scheduler entry. Mouse Unlock will no longer start on login.

### Change your pattern
Run setup again — it will ask to overwrite the existing config:

```
python <path-to-MouseUnlock-folder>\setup.py
```

---

## How the Lock Screen Works

1. `mouse_unlock.py` starts and registers a global hotkey listener (`pynput.keyboard.GlobalHotKeys`) on a background thread
2. When the hotkey is pressed, a message is sent via `queue.Queue` to the main thread
3. The main thread creates a `tkinter` fullscreen window:
   - Black background, no title bar (`overrideredirect=True`)
   - Always on top (`topmost=True`)
   - Grabs all input (`grab_set()`) — blocks Alt+Tab and other window switches
   - Shows current time (updates every second)
4. Each mouse click (left = `L`, right = `R`) is appended to a list
5. Once the list length matches `pattern_length`, the SHA256 hash is computed and compared
6. Match → green checkmark, window closes after 380ms
7. No match (or too many clicks) → red `✗`, resets after 1.1 seconds

---

## Limitations

- **Task Manager** (`Ctrl+Shift+Esc`) can still kill the process — this is a convenience tool, not a security replacement for Windows Hello or a password
- The actual **Windows lock screen** (`Win+L`) is separate — this app provides its own overlay lock screen
- Requires Python to be installed on the machine

---

## Tech Stack

| Component | Library / Tool |
|-----------|---------------|
| Mouse & keyboard input | `pynput` |
| Lock screen UI | `tkinter` (built into Python) |
| Pattern security | `hashlib` SHA256 |
| Auto-start | Windows Task Scheduler (`schtasks`) |
| Thread communication | `queue.Queue` |
