# 🐾 Antigravity Desktop Pet

An interactive, responsive desktop companion & Quick Chat widget for **Google Antigravity** on Windows, compatible with ChatGPT Pet sprite sheet specifications.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?logo=windows)
![GUI](https://img.shields.io/badge/GUI-PyQt6-41CD52?logo=qt)
![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-orange)

---

## ✨ Features

- **Desktop Companion**: Floats smoothly on your screen with transparent background and rich sprite animations.
- **Multiple Built-in Pets**:
  - 🦊 **Hime (ฮิเมะ)**: White-haired fox girl companion (ChatGPT Work v2 specification with gaze tracking).
  - 🪷 **Swan (สวอน)**: Lilac-haired lady with lace parasol (Created with `create-pet` skill, S-Tier 100/100).
  - 🤖 **Agy Chibi**: Cyberpunk mascot with glowing cat ears and visor.
  - 🟦 **Codex**: Classic blue terminal robot (`>_`).
  - 🚀 **Agy Bot**: Antigravity cyber coding companion.
  - 🔘 **Mini Mode**: Compact floating pill with Quick Chat & Activity controls.
- **Antigravity Live State Sync**: Monitors active Antigravity conversations & transcripts to dynamically animate states (`idle`, `thinking`, `review / celebrate`, `waiting`, `failed`).
- **Integrated Quick Chat**: Send prompts through the Antigravity CLI without switching context. Pet chat keeps its own CLI conversation ID.
- **Modern Web Dashboard**: Configure scale, toggle auto-roaming, switch pets, view recent conversations, or upload custom sprite sheets at `http://127.0.0.1:21420/settings`.
- **Custom Pet Upload**: Supports ChatGPT Pet v1 (8×9 grid) and v2 (8×11 grid) PNG/WebP sprite sheets up to 20 MiB.
- **External Trigger API**: Trigger pet animations via HTTP or Python script (`python notify.py celebrate`).

---

## 🚀 Quick Start

### วิธีที่ 1: สำหรับผู้ใช้งานทั่วไป (Standalone .EXE - ไม่ต้องติดตั้ง Python)
1. ไปที่หน้า [GitHub Releases](https://github.com/Raririn01/antigravity_pet/releases) แล้วดาวน์โหลดไฟล์ `AntigravityPet-Windows.zip`
2. แตกไฟล์ ZIP ออกมา
3. ดับเบิลคลิกที่ **`AntigravityPet.exe`** เพื่อเริ่มเล่นได้ทันที!

> หรือหากต้องการคอมไพล์เป็นไฟล์ `.exe` เองในเครื่อง เพียงดับเบิลคลิกไฟล์ **`build_exe.bat`**

---

### วิธีที่ 2: สำหรับนักพัฒนา (Developer Mode / Run with Python)
#### สิ่งที่ต้องเตรียม
- **Windows 10 / 11**
- **Python 3.10+** (เลือก *"Add Python to PATH"* ขณะติดตั้ง)
- **Antigravity CLI (`agy`)**

#### ขั้นตอนการรัน
1. **Clone repository:**
   ```bash
   git clone https://github.com/Raririn01/antigravity_pet.git
   cd antigravity_pet
   ```
2. **ติดตั้ง Dependencies:**
   ดับเบิลคลิก `install.bat` หรือรัน:
   ```bash
   pip install -r requirements.txt
   ```
3. **เปิดใช้งานสัตว์เลี้ยง:**
   ดับเบิลคลิก `start_pet.bat` หรือ `run_pet.bat` (หรือสั่ง `python main.py`)

---

## 🎮 Controls & Shortcuts

| Action | Control | Description |
| :--- | :--- | :--- |
| **Move** | Left Click + Drag | Drag pet anywhere on your desktop. Position is saved automatically. |
| **Quick Chat** | Left Click | Open or close the message composer. |
| **Open Antigravity** | Double Click | Launch or focus Antigravity. |
| **Context Menu** | Right Click | Open context menu to access Settings, toggle Mini Mode, open Antigravity, or hide. |
| **Summon Pet** | `Win + Alt + P` | Global hotkey to bring pet to the front / focus Quick Chat. |
| **Instant Appshot** | `Win + Alt + S` | Capture active screen instantly and attach `@[assets/appshot_latest.png]` to chat. |
| **Compact Pet Bar** | Bottom pill | `[✎]` opens Quick Chat, the waveform opens Windows dictation, and `[⌄]` opens the Pet menu. |
| **Activity Tray** | Pet menu | Displays recent Antigravity work with status badges (`Running`, `Needs input`, `Ready`, `Blocked`). |
| **Context Autocomplete** | `@` / `$` tags | Lists files in this project and skills actually installed for Antigravity. |

---

Quick Chat uses a separate Antigravity CLI conversation. It does not insert a message into the currently open Antigravity desktop chat. The voice button starts Windows dictation (`Win + H`) in the composer; microphone availability depends on Windows settings.

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

This project is licensed under the Non-Commercial & Attribution License ([MIT-NC / CC BY-NC](LICENSE)) - Free for personal use, attribution required, commercial sale prohibited.
