# 📋 Desktop Pet - Linux & Cross-Platform Porting Requirements
**เอกสารข้อกำหนดและขั้นตอนการปรับแต่งสำหรับรันบน Linux (Ubuntu, CachyOS/Arch) และ macOS**

---

## 1. System Requirements & Package Dependencies

### 🐧 A. Ubuntu / Debian (22.04 LTS, 24.04 LTS)
Ubuntu รุ่นใหม่เปิดใช้งาน PEP 668 (บล็อก `pip install` ระดับระบบ) และใช้ Wayland เป็นค่าเริ่มต้น ต้องติดตั้ง System Libraries สำหรับ Qt6 ดังนี้:

```bash
# อัปเดตแพ็กเกจและติดตั้งระบบพื้นฐาน
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    libxcb-cursor0 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxkbcommon-x11-0 \
    libgl1 \
    libglib2.0-0
```

### 🏹 B. CachyOS / Arch Linux
CachyOS และ Arch Linux ใช้ Pacman และมีแพ็กเกจ Qt6 ที่สมบูรณ์มาก:

```bash
sudo pacman -S --needed \
    python \
    python-pip \
    libxcb \
    xcb-util-cursor \
    xcb-util-image \
    xcb-util-keysyms \
    xcb-util-renderutil \
    xcb-util-wm \
    libxkbcommon \
    qt6-base \
    mesa
```

### 🍏 C. macOS (Apple Silicon / Intel)
```bash
brew install python@3.11
# หมายเหตุ: macOS ต้องเปิด Accessibility Permission ใน:
# System Settings -> Privacy & Security -> Accessibility ให้ Terminal หรือ Python
```

---

## 2. Python Dependencies (`requirements.txt`)

```text
PyQt6>=6.4.0
Pillow>=10.0.0
# ออปชันเสริมสำหรับ Global Hotkey ข้ามแพลตฟอร์ม:
# pynput>=1.7.6
```

---

## 3. Code Modification Checklist (สิ่งที่ต้องแก้ในโค้ด)

### ✅ Task 1: กำจัด Win32 Crash ใน `pet_window.py`
- [ ] **Import Guard**:
  ```python
  import sys
  if sys.platform == "win32":
      import ctypes
      from ctypes import wintypes
  ```
- [ ] **`_init_global_hotkey(self)` (บรรทัด ~1364)**:
  - ใส่เงื่อนไข `if sys.platform != "win32": return` หรือสลับไปใช้ `pynput` เพื่อไม่ให้เรียก `ctypes.windll.user32` จนแอปแครชตั้งแต่เริ่ม
- [ ] **`toggle_voice_mode(self)` (บรรทัด ~1100)**:
  - มี `if sys.platform == "win32":` อยู่แล้ว แต่ต้องระวังไม่ให้โค้ดส่วนอื่นเรียก `user32`

---

### ✅ Task 2: เปลี่ยน `os.startfile` เป็น Cross-Platform Opener
คำสั่ง `os.startfile` มีเฉพาะ Windows ต้องสร้าง Helper function ใน `pet_window.py` และ `antigravity_bridge.py`:

```python
import subprocess
import sys

def open_path_or_url(target: str):
    """เปิดไฟล์ โฟลเดอร์ หรือ URL รองรับ Windows, macOS, Linux"""
    if sys.platform == "win32":
        os.startfile(target)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", target])
    else:  # Linux (Ubuntu, CachyOS, etc.)
        subprocess.Popen(["xdg-open", target])
```
- [ ] แทนที่ `os.startfile(ag_path)` ใน `pet_window.py` (บรรทัด ~1416)
- [ ] แทนที่ `os.startfile(app_path)` ใน `antigravity_bridge.py` (บรรทัด ~594)

---

### ✅ Task 3: แก้ไข Path Resolution (ไม่ผูกกับ AppData/Local)
- [ ] **Antigravity CLI Discovery (`agy`)**:
  ให้หาจาก `shutil.which("agy")` เป็นหลักก่อนเสมอ:
  ```python
  import shutil

  def find_agy_cli() -> str:
      cli = shutil.which("agy")
      if cli:
          return cli
      home = os.path.expanduser("~")
      if sys.platform == "win32":
          return os.path.join(os.environ.get("LOCALAPPDATA", ""), "agy", "bin", "agy.exe")
      elif sys.platform == "darwin":
          candidates = ["/usr/local/bin/agy", os.path.join(home, ".local", "bin", "agy")]
      else:  # Linux
          candidates = [
              os.path.join(home, ".local", "bin", "agy"),
              "/usr/local/bin/agy",
              "/usr/bin/agy"
          ]
      for p in candidates:
          if os.path.isfile(p):
              return p
      return "agy"
  ```
- [ ] **User Profile Path**:
  แทนที่ `os.environ.get("USERPROFILE")` ให้ใช้ `os.path.expanduser("~")` เสมอ ซึ่งรองรับทั้ง `$HOME` บน Linux/Mac และ `%USERPROFILE%` บน Windows อัตโนมัติ

---

### ✅ Task 4: แก้ปัญหา Wayland Display Server (Ubuntu / CachyOS)
Wayland บล็อก `FramelessWindowHint`, `WindowStaysOnTopHint`, การอ่านพิกัดเมาส์ทั่วจอ (`QCursor.pos()`) และ `window.move()`
- [ ] **บังคับรันผ่าน XWayland (xcb)** ใน `main.py` ก่อนเริ่ม `QApplication`:
  ```python
  if sys.platform.startswith("linux"):
      # บังคับใช้ xcb (XWayland) เพื่อให้ลอยหน้าต่าง โปร่งใส และลากได้อย่างอิสระ
      os.environ.setdefault("QT_QPA_PLATFORM", "xcb;wayland")
  ```

---

## 4. Automation Shell Scripts

### 📄 `install.sh`
```bash
#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "=== ติดตั้ง Antigravity Desktop Pet สำหรับ Linux / macOS ==="

# สร้าง Virtual Environment เพื่อเลี่ยงปัญหา PEP 668
if [ ! -d "venv" ]; then
    echo "กำลังสร้าง python virtual environment (venv)..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "=== ติดตั้งเสร็จสมบูรณ์! รันด้วย ./run_pet.sh ==="
```

### 📄 `run_pet.sh`
```bash
#!/usr/bin/env bash
cd "$(dirname "$0")"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

# บน Linux ให้ตั้งค่ารันผ่าน xcb เพื่อรองรับ Wayland compositor
if [ "$(uname)" = "Linux" ]; then
    export QT_QPA_PLATFORM="xcb;wayland"
fi

python3 main.py "$@"
```

---

## 5. Quick Verification Steps บน Linux
1. ทดสอบว่า PyQt6 โหลด libxcb สำเร็จหรือไม่:
   ```bash
   python3 -c "from PyQt6.QtWidgets import QApplication; app = QApplication([]); print('PyQt6 OK')"
   ```
2. ทดสอบว่า Antigravity CLI พร้อมทำงาน:
   ```bash
   which agy
   agy --version
   ```
3. สั่งรัน Desktop Pet:
   ```bash
   chmod +x run_pet.sh
   ./run_pet.sh
   ```
