"""
Generates the Codex pet spritesheet conforming strictly to ChatGPT Pet v1 specification:
- Codex: The original blue robot companion with rounded cube body and '>_' LED face.
- Dimensions: 1536 x 1872 px (8 columns x 9 rows, cells 192 x 208)
- Transparent background (RGBA)
"""

import math
import os
from PIL import Image, ImageDraw

CELL_W = 192
CELL_H = 208
SHEET_W = 1536
SHEET_H = 1872

def draw_codex_face(draw: ImageDraw.ImageDraw, cx: int, cy: int, eye_style: str = "normal"):
    # Codex Screen (Dark Navy/Black)
    draw.rounded_rectangle([cx - 28, cy - 14, cx + 28, cy + 14], radius=8, fill=(15, 23, 42, 255), outline=(59, 130, 246, 200), width=1)
    
    col = (56, 189, 248, 255)  # Cyan LED
    
    if eye_style == "blink":
        draw.line([(cx - 14, cy), (cx - 4, cy)], fill=col, width=2)
        draw.line([(cx + 4, cy), (cx + 14, cy)], fill=col, width=2)
    elif eye_style == "happy":
        draw.arc([cx - 16, cy - 6, cx - 4, cy + 6], 200, 340, fill=col, width=2)
        draw.arc([cx + 4, cy - 6, cx + 16, cy + 6], 200, 340, fill=col, width=2)
    elif eye_style == "sleep":
        draw.line([(cx - 14, cy + 2), (cx - 4, cy + 2)], fill=(148, 163, 184, 255), width=2)
        draw.line([(cx + 4, cy + 2), (cx + 14, cy + 2)], fill=(148, 163, 184, 255), width=2)
    elif eye_style == "curious":
        # > ?
        draw.line([(cx - 16, cy - 5), (cx - 8, cy)], fill=col, width=2)
        draw.line([(cx - 8, cy), (cx - 16, cy + 5)], fill=col, width=2)
        draw.arc([cx + 6, cy - 8, cx + 14, cy], 180, 360, fill=col, width=2)
        draw.line([(cx + 14, cy - 4), (cx + 10, cy + 2)], fill=col, width=2)
        draw.ellipse([cx + 9, cy + 4, cx + 11, cy + 6], fill=col)
    else:  # Normal "> _" Codex iconic face
        # ">"
        draw.line([(cx - 16, cy - 5), (cx - 8, cy)], fill=col, width=2)
        draw.line([(cx - 8, cy), (cx - 16, cy + 5)], fill=col, width=2)
        # "_"
        draw.line([(cx + 4, cy + 4), (cx + 16, cy + 4)], fill=col, width=2)


def draw_codex(
    canvas: Image.Image,
    col: int,
    row: int,
    hover_y: float = 0,
    eye_style: str = "normal",
    hand_left: tuple = (-32, 14),
    hand_right: tuple = (32, 14),
    show_laptop: bool = False,
    show_zzz: int = 0,
    show_hearts: bool = False,
    show_confetti: int = 0,
    tilt_x: float = 0
):
    cell_x = col * CELL_W
    cell_y = row * CELL_H
    cell = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(cell)

    cx = CELL_W // 2 + int(tilt_x)
    cy = CELL_H // 2 + 10 + int(hover_y)

    # Shadow
    draw.ellipse([CELL_W // 2 - 32, CELL_H - 24, CELL_W // 2 + 32, CELL_H - 12], fill=(30, 41, 59, 70))

    # Thruster glow
    draw.ellipse([cx - 12, cy + 30, cx + 12, cy + 38], fill=(96, 165, 250, 180))
    draw.ellipse([cx - 6, cy + 30, cx + 6, cy + 35], fill=(255, 255, 255, 230))

    # Antenna
    draw.line([(cx, cy - 35), (cx, cy - 48)], fill=(37, 99, 235, 255), width=3)
    draw.ellipse([cx - 5, cy - 54, cx + 5, cy - 46], fill=(96, 165, 250, 255), outline=(29, 78, 216, 255), width=2)

    # Rounded Cube Body (Cobalt Blue Codex style)
    draw.rounded_rectangle(
        [cx - 36, cy - 32, cx + 36, cy + 32],
        radius=18,
        fill=(59, 130, 246, 255),
        outline=(29, 78, 216, 255),
        width=3
    )

    # Face screen
    draw_codex_face(draw, cx, cy, eye_style)

    # Hands
    hlx, hly = cx + hand_left[0], cy + hand_left[1]
    hrx, hry = cx + hand_right[0], cy + hand_right[1]
    draw.ellipse([hlx - 7, hly - 7, hlx + 7, hly + 7], fill=(147, 197, 253, 255), outline=(29, 78, 216, 255), width=2)
    draw.ellipse([hrx - 7, hry - 7, hrx + 7, hry + 7], fill=(147, 197, 253, 255), outline=(29, 78, 216, 255), width=2)

    # Props
    if show_laptop:
        lx = cx - 20
        ly = cy + 16
        draw.polygon([(lx, ly + 14), (lx + 40, ly + 14), (lx + 32, ly + 5), (lx + 8, ly + 5)], fill=(30, 41, 59, 255))
        draw.polygon([(lx + 6, ly + 4), (lx + 34, ly + 4), (lx + 34, ly - 16), (lx + 6, ly - 16)], fill=(15, 23, 42, 255), outline=(59, 130, 246, 255), width=1)
        draw.line([(lx + 10, ly - 11), (lx + 24, ly - 11)], fill=(56, 189, 248, 255), width=2)
        draw.line([(lx + 10, ly - 6), (lx + 30, ly - 6)], fill=(74, 222, 128, 255), width=2)

    if show_zzz > 0:
        for idx in range(show_zzz):
            zx = cx + 22 + idx * 8
            zy = cy - 20 - idx * 12
            draw.line([(zx, zy), (zx + 6, zy)], fill=(148, 163, 184, 220), width=2)
            draw.line([(zx + 6, zy), (zx, zy + 6)], fill=(148, 163, 184, 220), width=2)
            draw.line([(zx, zy + 6), (zx + 6, zy + 6)], fill=(148, 163, 184, 220), width=2)

    if show_hearts:
        hx, hy = cx + 28, cy - 24
        draw.polygon([(hx, hy + 10), (hx - 8, hy + 2), (hx - 8, hy - 5), (hx - 2, hy - 8), (hx, hy - 4), (hx + 2, hy - 8), (hx + 8, hy - 5), (hx + 8, hy + 2)], fill=(244, 114, 182, 255))

    if show_confetti > 0:
        colors = [(250, 204, 21, 255), (96, 165, 250, 255), (74, 222, 128, 255), (244, 114, 182, 255)]
        points = [(cx - 32, cy - 26), (cx + 34, cy - 30), (cx - 24, cy - 44), (cx + 26, cy - 48)]
        for i, (px, py) in enumerate(points[:show_confetti * 2]):
            c = colors[i % len(colors)]
            draw.line([(px - 3, py), (px + 3, py)], fill=c, width=2)
            draw.line([(px, py - 3), (px, py + 3)], fill=c, width=2)

    canvas.paste(cell, (cell_x, cell_y), cell)


def generate_codex_spritesheet(output_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    sheet = Image.new("RGBA", (SHEET_W, SHEET_H), (0, 0, 0, 0))

    # Row 0: Idle (6 frames)
    for col in range(6):
        hover = math.sin((col / 6.0) * 2 * math.pi) * 5
        eye = "blink" if col in (2, 3) else "normal"
        draw_codex(sheet, col=col, row=0, hover_y=hover, eye_style=eye)

    # Row 1: Walk (8 frames)
    for col in range(8):
        tilt = math.sin((col / 8.0) * 2 * math.pi) * 6
        hover = abs(math.sin((col / 8.0) * 2 * math.pi)) * -8
        draw_codex(sheet, col=col, row=1, hover_y=hover, tilt_x=tilt, hand_left=(-32, 14 + int(tilt)), hand_right=(32, 14 - int(tilt)))

    # Row 2: Work (8 frames)
    for col in range(8):
        hl_y = 8 if (col % 2 == 0) else 16
        hr_y = 16 if (col % 2 == 0) else 8
        draw_codex(sheet, col=col, row=2, hover_y=-2, hand_left=(-14, hl_y), hand_right=(14, hr_y), show_laptop=True)

    # Row 3: Sleep (4 frames)
    for col in range(4):
        hover = 14 + math.sin((col / 4.0) * 2 * math.pi) * 2
        draw_codex(sheet, col=col, row=3, hover_y=hover, eye_style="sleep", show_zzz=(col % 3) + 1)

    # Row 4: Wake (5 frames)
    for col in range(5):
        hover = 10 - col * 3
        eye = "sleep" if col < 2 else ("blink" if col == 2 else "normal")
        draw_codex(sheet, col=col, row=4, hover_y=hover, eye_style=eye)

    # Row 5: Play (8 frames)
    for col in range(8):
        angle = (col / 8.0) * 2 * math.pi
        hover = -14 + math.sin(angle) * 6
        draw_codex(sheet, col=col, row=5, hover_y=hover, eye_style="happy", hand_left=(-30 + math.cos(angle) * 10, 8 + math.sin(angle) * 10), hand_right=(30 - math.cos(angle) * 10, 8 - math.sin(angle) * 10))

    # Row 6: Happy (6 frames)
    for col in range(6):
        hover = -6 + (col % 2) * -6
        draw_codex(sheet, col=col, row=6, hover_y=hover, eye_style="happy", show_hearts=True)

    # Row 7: Curious (6 frames)
    for col in range(6):
        tilt = 5 if col >= 2 else 0
        draw_codex(sheet, col=col, row=7, hover_y=0, tilt_x=tilt, eye_style="curious")

    # Row 8: Celebrate (6 frames)
    for col in range(6):
        hover = -12 + math.sin((col / 6.0) * 2 * math.pi) * 5
        draw_codex(sheet, col=col, row=8, hover_y=hover, eye_style="happy", hand_left=(-26, -14), hand_right=(26, -14), show_confetti=min(2, col + 1))

    sheet.save(output_path, "PNG")
    print(f"Generated Codex spritesheet at: {output_path}")

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "assets", "codex_pet.png")
    generate_codex_spritesheet(out)
