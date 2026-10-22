# Antigravity Desktop Pet: แผนการปรับปรุงสู่มาตรฐาน ChatGPT Pets (Parity Roadmap)

เอกสารสรุปรายการสิ่งที่ต้องปรับปรุง (TODO / Action Items) เพื่อยกระดับ **Antigravity Desktop Pet** ให้เทียบเท่ามาตรฐานของ **ChatGPT / Codex Pets** ตามข้อกำหนดทางการ ([ChatGPT Pets Documentation](https://learn.chatgpt.com/docs/pets))

---

## 📊 ตารางเปรียบเทียบสถานะปัจจุบัน vs. ChatGPT Specification

| หมวดหมู่ | ChatGPT Desktop Pet | Antigravity Desktop Pet ปัจจุบัน | สถานะ | ลำดับความสำคัญ |
| :--- | :--- | :--- | :---: | :---: |
| **1. Activity Tray** | มีปุ่มกระดิ่ง 🔔 เปิดถาดลอย แสดงเธรดงานย่อย | ดูผ่านเว็บเบราว์เซอร์หรือปุ่ม Dropdown เท่านั้น | ❌ ยังไม่มี | **P0 (ด่วนที่สุด)** |
| **2. Status Lifecycle** | 4 สถานะมาตรฐาน (`Running`, `Needs input`, `Ready`, `Blocked`) | มี `thinking`, `review`, `sleep` (ไม่แยก Error/Waiting) | ⚠️ มีบางส่วน | **P0 (ด่วนที่สุด)** |
| **3. Sprite Animation** | ใช้ Row 5 (`failed`), Row 6 (`waiting`), Row 7 (`thinking`), Row 8 (`review`) | ใช้ Row 7 (`thinking`) และ Row 8 (`review`) เป็นหลัก | ⚠️ มีสไปรท์แต่ยังไม่ผูกสเตท | **P0 (ด่วนที่สุด)** |
| **4. Floating Controls** | Glassmorphic Bar มีปุ่ม New Chat, Voice, Bell | มี Hover Pill แยก และแถบ Quick Chat แยกกัน | ⚠️ ฟังก์ชันมีแต่ UI ยังไม่รวมศูนย์ | **P1 (สำคัญมาก)** |
| **5. Context & Skill Tags** | รองรับ `@` (เลือก Context) และ `$` (เลือก Skill) | เมนู Dropdown ปุ่ม `+` | ⚠️ ทำงานผ่านเมนูคลิก | **P1 (สำคัญมาก)** |
| **6. Mini Mode** | โหมดซ่อนตัวสไปรท์ เหลือเฉพาะแถบควบคุมลอย | มีฟังก์ชันซ่อนบางส่วน ยังไม่แยกเป็นโหมดสมบูรณ์ | ⚠️ ต้องปรับปรุง | **P1 (สำคัญมาก)** |
| **7. Appshots** | กดคีย์ลัดถ่ายภาพหน้าต่างปัจจุบันส่งเข้าแชท | ยังไม่มีระบบจับภาพหน้าจอ | ❌ ยังไม่มี | **P2 (สำคัญ)** |
| **8. AI Pet Creation** | ปุ่ม "Create Pet" สั่ง AI เจนสไปรท์ให้อัตโนมัติ | ให้อัปโหลดไฟล์ภาพเองผ่านหน้าเว็บ | ⚠️ มีสกิลแต่ยังไม่เชื่อม UI | **P2 (สำคัญ)** |
| **9. Voice Chat** | กดปุ่มคลื่นเสียงคุยโต้ตอบด้วยเสียงสด | ยังไม่มี Voice Input | ❌ ยังไม่มี | **P3 (ส่วนเสริม)** |

---

## 🎯 แผนการพัฒนาทีละเฟส (Implementation Phases)

### เฟส 1: ระบบถาดงาน (Activity Tray) และสถานะ 4 ระดับ (P0 - สำคัญที่สุด)
> **เป้าหมาย:** สัตว์เลี้ยงต้องทำหน้าที่เป็น Companion คอยรายงานและแจ้งเตือนงานที่ทำอยู่ในพื้นหลังได้แบบเรียลไทม์

- [x] **1.1 ปรับระบบสถานะ (Status Lifecycle Mapping)**
  - เพิ่มสถานะมาตรฐาน 4 ตัวใน `antigravity_bridge.py`:
    - `Running`: งานกำลังประมวลผล (Thinking / Tool Calling)
    - `Needs input`: รอการตัดสินใจของผู้ใช้ (เช่น การยืนยัน Tool, คำถามจาก `ask_question`)
    - `Ready`: ทำงานเสร็จเรียบร้อยแล้วและยังไม่ได้เปิดอ่าน (พร้อมติ๊กถูกสีเขียว)
    - `Blocked`: เกิดข้อผิดพลาด หรือหยุดการทำงานเนื่องจากระบบล้มเหลว (Error)
  - ผูกสเตทเข้ากับแถวแอนิเมชันของ Sprite Sheet:
    - `Needs input` $\rightarrow$ สลับไปเล่นท่า **Row 6 (`waiting`)**
    - `Blocked` $\rightarrow$ สลับไปเล่นท่า **Row 5 (`failed`)**
    - `Ready` $\rightarrow$ สลับไปเล่นท่า **Row 8 (`review`)** หรือ **Row 3 (`waving`)**
    - `Running` $\rightarrow$ สลับไปเล่นท่า **Row 7 (`thinking`)**

- [x] **1.2 การจัดลำดับความสำคัญของเธรด (Thread Prioritization)**
  - เมื่อมีหลายบทสนทนาทำงานพร้อมกัน ให้เรียงลำดับเธรดที่จะขึ้นเตือนบนตัวสัตว์เลี้ยง:
    $$\text{Needs input} \succ \text{Blocked} \succ \text{Ready} \succ \text{Running}$$

- [x] **1.3 สร้าง Floating Activity Tray Widget ใน `pet_window.py`**
  - เพิ่มปุ่มกระดิ่ง 🔔 ที่ Floating Bar
  - เมื่อกดกระดิ่ง ให้เปิดการ์ดแสดงรายการ 3-5 เธรดล่าสุดลอยอยู่ใต้ตัวน้อง
  - แต่ละรายการแสดง:
    - ชื่อหัวข้อบทสนทนา (Truncated Title)
    - Badge สถานะสี (`สีเหลือง = Needs input`, `สีแดง = Blocked`, `สีเขียว = Ready`, `สีฟ้า = Running`)
    - ข้อความสรุปสั้นๆ (เช่น *"Your checklist is ready."*)
  - คลิกที่เธรดเพื่อเปิดหน้าต่าง Antigravity 2.0 ไปยังบทสนทนานั้น
  - มีปุ่ม Chevron ⌵ สำหรับพับเก็บถาด

---

### เฟส 2: ออกแบบ Floating Controls ให้เป็น Glassmorphic Capsule (P1)
> **เป้าหมาย:** ประสบการณ์การใช้งานลื่นไหลและดูทันสมัยเหมือน ChatGPT Desktop App

- [x] **2.1 รวมแถบควบคุมใต้ตัวน้องเป็น Floating Glass Bar เดียว**
  - **โหมดพับ (Collapsed Bar):**
    - `[✎]` ปุ่มเปิดกล่องพิมพ์เริ่มแชทใหม่
    - `[🎙]` ปุ่มไอคอนเสียง (Voice/Mic)
    - `[🔔]` ปุ่มเปิด Activity Tray พร้อมจุดแจ้งเตือน (Notification Dot) เมื่อมีงานสถานะ `Ready` หรือ `Needs input`
  - **โหมดพิมพ์ (Expanded Composer):**
    - กางแถบ input สวยงามโดยที่ตำแหน่งตัวสัตว์เลี้ยงไม่กระตุก
    - คงปุ่ม `+` และปุ่มลูกศรส่ง `↑`

- [x] **2.2 รองรับสัญลักษณ์ `@` และ `$` ในกล่องข้อความ**
  - เมื่อพิมพ์ `@` ให้แสดง Auto-complete popup เลือกไฟล์ล่าสุดใน Workspace
  - เมื่อพิมพ์ `$` ให้แสดง Auto-complete popup เลือก Skills ที่มีในระบบ

- [x] **2.3 โหมด Mini (No-pet Mode)**
  - เพิ่มตัวเลือกในเมนูคลิกขวาและหน้า Settings: **"โหมด Mini (ซ่อนสัตว์เลี้ยง เหลือเฉพาะแถบควบคุม)"**
  - ยุบขนาดหน้าต่างเหลือเฉพาะ Floating Bar ลอยอยู่ที่มุมจอตามที่ผู้ใช้ลากวางไว้

---

### เฟส 3: ระบบจับภาพหน้าต่างปัจจุบัน (Appshots) (P2)
> **เป้าหมาย:** สั่งงาน AI ได้ทันทีจากหน้าจอที่กำลังเปิดทำงานอยู่

- [x] **3.1 ฟังก์ชันแคปภาพหน้าจอหน้าต่างที่ใช้งานอยู่ (Active Window Grab)**
  - ดึงภาพหน้าจอปัจจุบันด้วย native PyQt6 `primaryScreen().grabWindow(0)` รวดเร็วและเสถียร
  - บันทึกภาพลง `assets/appshot_latest.png` และแนบแท็ก `@[assets/appshot_latest.png] ` เข้าช่องพิมพ์
- [x] **3.2 คีย์ลัดสากลสำหรับ Appshots**
  - รองรับ Hotkey `Win + Alt + S` เพื่อแคปภาพหน้าจอทันที พร้อมปุ่มไอคอนกล้อง 📷 ในกล่องข้อความ

---

### เฟส 4: ระบบสั่งสร้างสัตว์เลี้ยงด้วย AI ("Create Pet with AI") (P2)
> **เป้าหมาย:** สร้างตัวละครใหม่ได้ในคลิกเดียวโดยไม่ต้องวาดสไปรท์ชีตเอง

- [x] **4.1 เพิ่มปุ่ม "Create Pet with AI" ในหน้าเว็บ Settings (`settings.html`)**
  - มีกล่องข้อความให้ผู้ใช้กรอก Prompt บรรยายสัตว์เลี้ยง เช่น:
    > *"ลูกแมวสีส้มสไตล์พิกเซลอาร์ต สวมหมวกพ่อมดจิ๋ว"*
- [x] **4.2 เชื่อมต่อกับ Pipeline สกิล `create-pet`**
  - เชื่อมโยงผ่าน `POST /api/create-pet-ai` พร้อมตัวเจนสไปรท์ชีต 9 แถว 8 คอลัมน์ (1536x1872) ที่ผ่าน validation 100%
  - เพิ่มตัวละครใหม่เข้า `custom_pets.json` และรีเฟรชใช้งานได้ทันที

---

### เฟส 5: สั่งงานด้วยเสียง (Voice Input Integration) (P3 - ตัวเลือกเสริม)
- [x] เพิ่มปุ่ม Voice `[🎙]` บน Floating Capsule Bar
- [x] เชื่อมต่อระบบเสียงจำลอง/เตรียมพร้อม Voice Chat พร้อม Notification indicator

---

## 🛠️ แผนผังการแก้ไขโค้ด (File Modification Map)

```mermaid
flowchart TD
    A["pet_window.py (GUI & Window)"] -->|1. เพิ่มปุ่มกระดิ่ง & Floating Activity Card| B["Activity Tray UI"]
    A -->|2. เพิ่ม Glassmorphic Floating Controls| C["Pill Bar Redesign"]
    A -->|3. ปรับปรุงโหมด Mini แบบสมบูรณ์| D["Mini Mode"]
    
    E["antigravity_bridge.py (Bridge & Watcher)"] -->|1. วิเคราะห์สถานะ 4 แบบ| F["Status Engine"]
    F -->|Running / Needs input / Ready / Blocked| A
    E -->|2. จัดลำดับความสำคัญของเธรด| B
    
    G["spritesheet.py"] -->|แมปท่า waiting (Row 6) และ failed (Row 5)| A
    
    H["settings.html"] -->|เพิ่มตัวเลือก Mini Mode และปุ่ม Create Pet with AI| I["Web Settings"]
```

---

## 📋 เช็คลิสต์ตรวจสอบความสำเร็จ (Definition of Done)
- [x] มีปุ่มกระดิ่ง 🔔 ที่กดแล้วแสดงรายการงานย่อยพร้อมสถานะ `Running`, `Needs input`, `Ready`, `Blocked`
- [x] ตัวสัตว์เลี้ยงแสดงท่าทางหงอย/ล้มเหลว (`failed`) เมื่องาน Error และแสดงท่ารอคอย (`waiting`) เมื่องานรอให้อนุมัติ
- [x] เมื่อกด `Win + Alt + P` หน้าต่างจะโฟกัสที่ช่องพิมพ์และเปิดแถบควบคุมอย่างรวดเร็ว
- [x] สามารถสลับไปใช้โหมด Mini ได้อย่างราบรื่นโดยไม่เหลือพื้นที่ว่างของ Canvas
- [x] ข้อมูลทุกอย่างยังคงซิงค์ตรงกับ Antigravity 2.0 อย่างถูกต้อง
