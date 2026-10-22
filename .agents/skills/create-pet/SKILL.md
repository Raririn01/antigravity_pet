---
name: create-pet
description: >-
  Standard workflow to create, validate, slice, preview, benchmark, and package
  animation sprite sheets for Antigravity & ChatGPT-compatible Desktop Pets
  (v1 1536x1872 px 9 rows, v2 1536x2288 px 11 rows with 16-direction gaze tracking).
  Enforces the Hime Gold Standard for zero-jitter and sub-pixel quality.
---

# Create Desktop Pet Skill (Hime Gold Standard Edition)

This skill defines the complete pipeline and quality criteria to create, inspect, validate, and benchmark animated desktop companion pets. It sets **Hime (`assets/hime_pet.png`)** as the **S-Tier Gold Standard Benchmark** that every pet must strive to match.

---

## 🏆 The Hime Gold Standard (เกณฑ์คุณภาพระดับฮิเมะ 100/100)

Hime sets the bar for desktop pets with the following verifiable quality metrics:

1. **Zero-Jitter Baseline (ล็อคระดับเท้าแม่นยำระดับพิกเซล)**:
   - ส้นเท้า/ชายกระโปรงของตัวละครในแถวที่ยืนพื้น (idle, waving, failed, waiting, thinking, review, look-1, look-2) ต้องแตะที่พิกัดระดับเดียวกันอย่างแน่นอน (`Y = 203 px` ภายในเซลล์สูง 208 px) โดยมีค่ากระจาย (spread) **ไม่เกิน 1 px**
   - ห้ามมีอาการตัวละครเด้งขึ้นเด้งลง (jitter/wobble) ขณะลูปแอนิเมชัน
2. **Sub-Pixel Horizontal Centering (กึ่งกลางสมมาตร X = 96.0 px)**:
   - แกนกลางตัวละครต้องอยู่ตรงกลางเซลล์พอดี (`X = 96.0 px` ของเซลล์กว้าง 192 px) เบี่ยงเบนเฉลี่ยไม่เกิน 1.0 px เพื่อให้เวลาหมุนตัวหรือสลับทิศทางไม่แกว่ง
3. **16-Direction Gaze Tracking (แถว 9-10 สายตามองตามเมาส์ 360°)**:
   - รองรับสเปก v2 (11 แถว) โดยแถว 9 และ 10 เป็นการเอียงหัวและขยับรูม่านตาอย่างละเอียดตามมุม 22.5° (16 ทิศทาง) สอดคล้องกับพิกัดเมาส์รอบตัว
4. **Artistic & Detail Consistency (ความคงเส้นคงวาของตัวละคร 100%)**:
   - ไม่ว่าตัวละครจะอยู่ในแอ็กชันใด (idle, วิ่ง, คิดงาน, ดีใจ) ดีเทลจุดจำของตัวละคร เช่น เครื่องประดับผม, ทรงผม, สีตา, หู, ลายผ้า ต้องคงเดิมอย่างแม่นยำ ไม่กลายพันธุ์
5. **Pristine Alpha Edge (ขอบภาพโปร่งใสสะอาดหมดจด)**:
   - ไม่มีขอบขาว (white halo) จากการตัดพื้นหลังหยาบ
   - ไม่มีขอบม่วง/เขียว (chroma fringe) จากการคีย์สี
   - ค่าความโปร่งใส (Alpha) คมชัดเนียนตา

---

## 📋 The 7-Step Pet Creation Standard

```
[1. Concept & Master Art] ──► [2. Standard Grid Layout] ──► [3. Frame Extraction & Cleanup]
                                                                        │
[6. Ingestion & Activation] ◄── [5. QA Benchmark Test] ◄── [4. Gaze & Animation QA]
            │
            ▼
[7. Asset Library Archival]
```

### 1. Concept, Character Description & Reference Art
- **Prompt / Visual Identity**: Define personality, costume, color scheme, and species traits.
- **Form Variations** (if applicable):
  - **General Form (ร่างทั่วไป)**: Idle, greeting, waiting, celebration (e.g. signature dress/kimono).
  - **Movement / Beast Form (ร่างการเคลื่อนไหว)**: Running, dash, jumping (e.g. four-legged fox form or flying mode).
  - **Work / Focus Form (ร่างโฟกัส/ทำงาน)**: Thinking, review, terminal hacking (e.g. scholar robe, golden outfit, or hacker visor).
- **Master Reference**: Generate or source high-resolution reference art on a solid or transparent background.

---

### 2. Standard Grid Specifications (192 × 208 px per cell)

Pets strictly adhere to one of two formats:
- **v1 Standard (Classic)**: `1536 × 1872 px` (8 columns × 9 rows)
- **v2 Advanced (Gaze Tracking)**: `1536 × 2288 px` (8 columns × 11 rows)

#### Row Mapping Table

| Row | Action Name | Required Frames | Purpose / Emotion | Trigger in Antigravity |
| :---: | :--- | :---: | :--- | :--- |
| **0** | `idle` | 6 | Calm breathing loop, resting state | AI agent idle |
| **1** | `running-right` | 8 | Directional run / walk to the right | Dragging pet right |
| **2** | `running-left` | 8 | Directional run / walk to the left | Dragging pet left |
| **3** | `waving` | 4 | Greeting, poke reaction, happy wave | Left click / Greet |
| **4** | `jumping` | 5 | Excitement, playful bounce | Playful poke |
| **5** | `failed` | 8 | Error reaction, sadness, dejection | Tool / Test error |
| **6** | `waiting` | 6 | Expectant request for approval / sleep | Awaiting user input |
| **7** | `thinking` | 6 | Active computation, writing code, work | Agent executing turn |
| **8** | `review` | 6 | Celebration, inspection, task passed | Task completed successfully |
| **9** | `look-1` *(v2)* | 8 | Cursor gaze: 0° to 157.5° (Top to Right) | Pointer hovering nearby |
| **10** | `look-2` *(v2)* | 8 | Cursor gaze: 180° to 337.5° (Bottom to Left) | Pointer hovering nearby |

---

### 3. Frame Extraction, Transparency & Despill
- **Chroma Key Removal**: If rendered against magenta (`#FF00FF`) or green screen, remove color cleanly.
- **Edge Despill**: Suppress color fringing along hair, ears, and transparent edges.
- **Ground Baseline Alignment**: Ensure character feet touch a consistent horizontal baseline across frames in each row (typically `y ≈ 200-203` inside each 208 px cell) to achieve 0px jitter.
- **Bounding Box Integrity**: Character must fit within the 192 × 208 cell without clipping ears, tails, or accessories.

---

### 4. Gaze Direction & Animation Continuity QA
- **Row 9 & 10 (16-Direction Gaze)**:
  - Each frame corresponds to a 22.5° angular slice.
  - Test cursor tracking: as mouse circles around the pet, pupils and head smoothly follow the pointer.
- **Loop Continuity**:
  - `idle`: Frame 5 must seamlessly loop back to Frame 0.
  - `running`: Cycles must be rhythmically consistent without sudden position jumps.
- **Multi-Form Consistency**: Verify that transformed states (e.g. fox running form) preserve key recognizers (ear tips, eye color, ribbons).

---

### 5. Automated Validation & Quality Benchmark
Always benchmark before deploying to ensure Hime-tier quality:

```bash
# 1. Benchmark quality score against the Hime Gold Standard (Target: >= 85/100)
python scripts/pet_tools.py benchmark path/to/pet_spritesheet.png

# 2. Validate compliance with v1/v2 spec
python scripts/pet_tools.py validate path/to/pet_spritesheet.png

# 3. Generate animated preview GIFs
python scripts/pet_tools.py preview path/to/pet_spritesheet.png --out ./previews
```

Expected benchmark output for high-quality pet:
```text
=== Pet Quality Benchmark (Hime Standard): assets/hime_pet.png ===
Overall Score: 100/100  -->  [S-Tier (Hime Gold Standard)]
Spec Version:  v2
Baseline Spread: 0px (Target: <= 1px)  [Points: 40/40]
Center Offset:   0.57px (Target: <= 1px)  [Points: 30/30]
Gaze Quality:    [Points: 20/20]
Alpha Fringe:    Halo ratio 0.00084  [Points: 10/10]
===========================================================
```

---

### 6. Ingestion & Activation
To activate the new pet:
1. **Via UI**: Open `http://127.0.0.1:21420/settings#upload` and upload the PNG/WebP file.
2. **Via Assets Directory**:
   - Save spritesheet as `assets/<pet_id>.png`
   - Save preview thumbnail as `assets/<pet_id>_preview.png`
   - Register entry in `assets/custom_pets.json` or `available_pets()` in `antigravity_bridge.py`.

---

### 7. Library Archival
Organize the master assets inside the companion archive or workspace:
```
library/
└── <pet_name>/
    ├── source_references/       # Master AI prompts, sketches, high-res renders
    ├── frames/                  # Sliced 192x208 frames (00_idle, 01_running, ...)
    ├── previews/                # Animated preview GIFs (idle.gif, walk.gif, ...)
    ├── validation_report.json   # Output from pet_tools.py validate --json
    ├── benchmark_report.json    # Output from pet_tools.py benchmark --json
    └── <pet_name>_v2.png        # Production 1536x2288 spritesheet
```

---

## 🛠️ CLI Toolkit Reference (`scripts/pet_tools.py`)

| Command | Syntax | Description |
| :--- | :--- | :--- |
| **benchmark** | `python scripts/pet_tools.py benchmark <file.png> [--json]` | Rates spritesheet against Hime Gold Standard (0-100 score, baseline jitter, center offset, alpha cleanliness). |
| **validate** | `python scripts/pet_tools.py validate <file.png> [--json]` | Verifies dimensions, RGBA transparency, and frame counts per row. |
| **preview** | `python scripts/pet_tools.py preview <file.png> [--out <dir>]` | Generates loopable animated GIFs for every row. |
| **slice** | `python scripts/pet_tools.py slice <file.png> [--out <dir>]` | Extracts all frames into organized folders by row and action. |
| **assemble** | `python scripts/pet_tools.py assemble <frames_dir> --out <file.png> [--version v1\|v2]` | Stitches sliced frames into a standard spritesheet. |
