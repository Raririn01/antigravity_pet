# 🐾 Antigravity Desktop Pet

An interactive, responsive desktop companion & Quick Chat widget for **Google Antigravity** on Windows, compatible with ChatGPT Pet sprite sheet specifications.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?logo=windows)
![GUI](https://img.shields.io/badge/GUI-PyQt6-41CD52?logo=qt)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Desktop Companion**: Floats smoothly on your screen with transparent background and rich sprite animations.
- **Multiple Built-in Pets**:
  - 🦊 **Hime (ฮิเมะ)**: White-haired fox girl companion (ChatGPT Work v2 specification with gaze tracking).
  - 🤖 **Agy Chibi**: Cyberpunk mascot with glowing cat ears and visor.
  - 🟦 **Codex**: Classic blue terminal robot (`>_`).
  - 🚀 **Agy Bot**: Antigravity cyber coding companion.
  - 🔘 **Mini Mode**: Compact floating pill with Quick Chat & Activity controls.
- **Antigravity Live State Sync**: Monitors active Antigravity conversations & transcripts to dynamically animate states (`idle`, `thinking`, `review / celebrate`, `waiting`, `failed`).
- **Integrated Quick Chat**: Send prompts directly to the Antigravity CLI in plan mode without switching context.
- **Modern Web Dashboard**: Configure scale, toggle auto-roaming, switch pets, view recent conversations, or upload custom sprite sheets at `http://127.0.0.1:21420/settings`.
- **Custom Pet Upload**: Supports ChatGPT Pet v1 (8×9 grid) and v2 (8×11 grid) PNG/WebP sprite sheets up to 20 MiB.
- **External Trigger API**: Trigger pet animations via HTTP or Python script (`python notify.py celebrate`).

---

## 🚀 Quick Start

### Prerequisites
- **Windows 10 / 11**
- **Python 3.10+** (Make sure to check *"Add Python to PATH"* during installation)
- *(Optional)* **Antigravity / Antigravity IDE** & CLI (`agy`) for transcript synchronization and Quick Chat.

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/desktop-pet.git
cd desktop-pet
```

### 2. Install dependencies
Double-click `install.bat` or run:
```bash
pip install -r requirements.txt
```

### 3. Launch Desktop Pet
Double-click `run_pet.bat` or run:
```bash
python main.py
```

---

## 🎮 Controls & Shortcuts

| Action | Control | Description |
| :--- | :--- | :--- |
| **Move** | Left Click + Drag | Drag pet anywhere on your desktop. Position is saved automatically. |
| **Poke / Greet** | Left Click | Play waving or poke animation. |
| **Celebrate** | Double Click | Play celebratory spin / review animation. |
| **Context Menu** | Right Click | Open context menu to access Settings, open Antigravity, or hide. |
| **Summon Pet** | `Win + Alt + P` | Global hotkey to bring pet to the front / focus. |
| **Mini Controls** | Hover | Reveals the mini pill (`[✎] Quick Chat` and `[॥] Settings & Activity`). |

---

## ⚙️ Settings & Web Dashboard

When the pet is running, open your browser to:
```
http://127.0.0.1:21420/settings
```
From the settings dashboard, you can:
- Adjust size & scale factor (0.5x – 2.0x)
- Enable/disable live Antigravity sync
- Enable/disable speech bubble status messages
- Toggle Auto-Roam behavior
- Upload, rename, test, and delete custom pet sprite sheets

---

## 🎨 Custom Pet Specification

Compatible with ChatGPT Pet sprite sheet specifications:
- **Cell Size**: 192 × 208 px per frame
- **Grid v1**: 1536 × 1872 px (8 columns × 9 rows)
  - Row 0: `idle` (6 frames)
  - Row 1: `running-right` (8 frames)
  - Row 2: `running-left` (8 frames)
  - Row 3: `waving` (4 frames)
  - Row 4: `jumping` (5 frames)
  - Row 5: `failed` (8 frames)
  - Row 6: `waiting` (6 frames)
  - Row 7: `thinking` (6 frames)
  - Row 8: `review` (6 frames)
- **Grid v2**: 1536 × 2288 px (Adds Rows 9 & 10 for 16-direction cursor gaze tracking).

---

## 📡 REST API & External Triggers

You can trigger pet states from your own build scripts, CI tools, or terminal:

```bash
# Using notify.py helper
python notify.py work "Compiling project..."
python notify.py celebrate "All tests passed!"
python notify.py curious "Review required"
python notify.py idle
```

Or via direct HTTP POST:
```bash
curl -X POST http://127.0.0.1:21420/state \
  -H "Content-Type: application/json" \
  -d "{\"state\":\"celebrate\",\"message\":\"Build Successful!\"}"
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
