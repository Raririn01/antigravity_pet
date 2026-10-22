"""
Generates Hime pet spritesheet conforming strictly to ChatGPT Pet v1 specification:
- Hime: จิ้งจอกสาวจิ๋วผมขาว ตาแดง ชุดแดงขาว และเครื่องประดับทอง
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

def draw_hime(
    canvas: Image.Image,
    col: int,
    row: int,
    hover_y: float = 0,
    eye_style: str = "normal",  # normal, blink, happy, sleep, wide, curious
    tail_swing: float = 0,
    hand_left: tuple = (-24, 20),
    hand_right: tuple = (24, 20),
    show_laptop: bool = False,
    show_zzz: int = 0,
    show_hearts: bool = False,
    show_confetti: int = 0,
    show_sakura: bool = False,
    tilt_x: float = 0
):
    cell_x = col * CELL_W
    cell_y = row * CELL_H
    cell = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(cell)

    cx = CELL_W // 2 + int(tilt_x)
    cy = CELL_H // 2 + 10 + int(hover_y)

    # Shadow
    draw.ellipse([CELL_W // 2 - 28, CELL_H - 24, CELL_W // 2 + 28, CELL_H - 12], fill=(30, 41, 59, 70))

    # Fluffy Fox Tail (White with Red tip)
    tx = cx + 22 + int(tail_swing * 12)
    ty = cy + 15
    draw.ellipse([tx - 12, ty - 22, tx + 20, ty + 18], fill=(248, 250, 252, 255), outline=(226, 232, 240, 255), width=2)
    draw.polygon([(tx + 6, ty - 22), (tx + 22, ty - 12), (tx + 18, ty - 5)], fill=(225, 29, 72, 255))

    # Red & White Kimono Dress
    draw.polygon([(cx - 20, cy + 12), (cx + 20, cy + 12), (cx + 26, cy + 38), (cx - 26, cy + 38)], fill=(225, 29, 72, 255))
    draw.polygon([(cx - 12, cy + 14), (cx + 12, cy + 14), (cx + 14, cy + 38), (cx - 14, cy + 38)], fill=(255, 255, 255, 255))
    # Gold Obi Ribbon
    draw.rectangle([cx - 18, cy + 22, cx + 18, cy + 27], fill=(245, 158, 11, 255))

    # Feet
    draw.ellipse([cx - 14, cy + 36, cx - 4, cy + 42], fill=(244, 63, 94, 255))
    draw.ellipse([cx + 4, cy + 36, cx + 14, cy + 42], fill=(244, 63, 94, 255))

    # Head (Cute Chibi anime style)
    draw.ellipse([cx - 28, cy - 26, cx + 28, cy + 16], fill=(254, 243, 199, 255))

    # Fox Ears (White fluffy ears with pink inner and red tips)
    # Left Ear
    draw.polygon([(cx - 20, cy - 18), (cx - 36, cy - 48), (cx - 8, cy - 28)], fill=(255, 255, 255, 255), outline=(225, 29, 72, 255), width=2)
    draw.polygon([(cx - 18, cy - 20), (cx - 30, cy - 42), (cx - 12, cy - 26)], fill=(251, 113, 133, 255))
    # Right Ear
    draw.polygon([(cx + 20, cy - 18), (cx + 36, cy - 48), (cx + 8, cy - 28)], fill=(255, 255, 255, 255), outline=(225, 29, 72, 255), width=2)
    draw.polygon([(cx + 18, cy - 20), (cx + 30, cy - 42), (cx + 12, cy - 26)], fill=(251, 113, 133, 255))

    # White Hair (Bangs & Twin Hair Side strands)
    draw.chord([cx - 30, cy - 30, cx + 30, cy + 6], 180, 360, fill=(255, 255, 255, 255))
    # Bangs
    draw.polygon([(cx - 26, cy - 18), (cx - 14, cy - 2), (cx - 4, cy - 18)], fill=(255, 255, 255, 255))
    draw.polygon([(cx - 8, cy - 18), (cx + 2, cy - 1), (cx + 12, cy - 18)], fill=(255, 255, 255, 255))
    draw.polygon([(cx + 6, cy - 18), (cx + 18, cy - 3), (cx + 26, cy - 18)], fill=(255, 255, 255, 255))

    # Gold Hair Ornaments
    draw.ellipse([cx - 24, cy - 22, cx - 18, cy - 16], fill=(245, 158, 11, 255))
    draw.ellipse([cx + 18, cy - 22, cx + 24, cy - 16], fill=(245, 158, 11, 255))

    # Red Anime Eyes
    red_col = (225, 29, 72, 255)
    lx, rx = cx - 12, cx + 12
    ey = cy - 4

    if eye_style == "blink":
        draw.line([(lx - 5, ey), (lx + 5, ey)], fill=red_col, width=2)
        draw.line([(rx - 5, ey), (rx + 5, ey)], fill=red_col, width=2)
    elif eye_style == "happy":
        draw.arc([lx - 6, ey - 5, lx + 6, ey + 5], 200, 340, fill=red_col, width=3)
        draw.arc([rx - 6, ey - 5, rx + 6, ey + 5], 200, 340, fill=red_col, width=3)
        draw.ellipse([lx - 10, ey + 6, lx - 4, ey + 10], fill=(251, 113, 133, 180))
        draw.ellipse([rx + 4, ey + 6, rx + 10, ey + 10], fill=(251, 113, 133, 180))
    elif eye_style == "sleep":
        draw.line([(lx - 6, ey + 1), (lx + 6, ey + 1)], fill=(148, 163, 184, 255), width=2)
        draw.line([(rx - 6, ey + 1), (rx + 6, ey + 1)], fill=(148, 163, 184, 255), width=2)
    elif eye_style == "curious":
        draw.ellipse([lx - 5, ey - 6, lx + 5, ey + 6], fill=red_col)
        draw.ellipse([lx - 2, ey - 4, lx + 2, ey], fill=(255, 255, 255, 255))
        draw.ellipse([rx - 6, ey - 7, rx + 6, ey + 7], fill=red_col)
        draw.ellipse([rx - 3, ey - 5, rx + 3, ey + 1], fill=(255, 255, 255, 255))
    else:  # normal
        draw.ellipse([lx - 5, ey - 6, lx + 5, ey + 6], fill=red_col)
        draw.ellipse([rx - 5, ey - 6, rx + 5, ey + 6], fill=red_col)
        draw.ellipse([lx - 2, ey - 4, lx + 2, ey], fill=(255, 255, 255, 255))
        draw.ellipse([rx - 2, ey - 4, rx + 2, ey], fill=(255, 255, 255, 255))
        draw.ellipse([lx - 9, ey + 6, lx - 4, ey + 10], fill=(251, 113, 133, 140))
        draw.ellipse([rx + 4, ey + 6, rx + 9, ey + 10], fill=(251, 113, 133, 140))

    # Cute Mouth
    my = cy + 5
    if eye_style == "happy":
        draw.arc([cx - 4, my - 2, cx + 4, my + 4], 20, 160, fill=red_col, width=2)
    else:
        draw.arc([cx - 3, my - 1, cx + 3, my + 3], 20, 160, fill=red_col, width=2)

    # Hands / Sleeves
    hlx, hly = cx + hand_left[0], cy + hand_left[1]
    hrx, hry = cx + hand_right[0], cy + hand_right[1]
    draw.ellipse([hlx - 6, hly - 6, hlx + 6, hly + 6], fill=(255, 255, 255, 255), outline=(225, 29, 72, 255), width=2)
    draw.ellipse([hrx - 6, hry - 6, hrx + 6, hry + 6], fill=(255, 255, 255, 255), outline=(225, 29, 72, 255), width=2)

    # Props
    if show_laptop:
        lx = cx - 20
        ly = cy + 18
        draw.polygon([(lx, ly + 14), (lx + 40, ly + 14), (lx + 32, ly + 5), (lx + 8, ly + 5)], fill=(225, 29, 72, 255))
        draw.polygon([(lx + 6, ly + 4), (lx + 34, ly + 4), (lx + 34, ly - 14), (lx + 6, ly - 14)], fill=(255, 241, 242, 255), outline=(225, 29, 72, 255), width=1)
        draw.line([(lx + 10, ly - 10), (lx + 24, ly - 10)], fill=(225, 29, 72, 255), width=2)
        draw.line([(lx + 10, ly - 5), (lx + 30, ly - 5)], fill=(245, 158, 11, 255), width=2)

    if show_zzz > 0:
        for idx in range(show_zzz):
            zx = cx + 22 + idx * 8
            zy = cy - 24 - idx * 12
            draw.line([(zx, zy), (zx + 6, zy)], fill=(251, 113, 133, 220), width=2)
            draw.line([(zx + 6, zy), (zx, zy + 6)], fill=(251, 113, 133, 220), width=2)
            draw.line([(zx, zy + 6), (zx + 6, zy + 6)], fill=(251, 113, 133, 220), width=2)

    if show_hearts:
        hx, hy = cx + 28, cy - 24
        draw.polygon([(hx, hy + 10), (hx - 8, hy + 2), (hx - 8, hy - 5), (hx - 2, hy - 8), (hx, hy - 4), (hx + 2, hy - 8), (hx + 8, hy - 5), (hx + 8, hy + 2)], fill=(244, 63, 94, 255))

    if show_confetti > 0 or show_sakura:
        colors = [(251, 113, 133, 255), (245, 158, 11, 255), (255, 255, 255, 255)]
        points = [(cx - 34, cy - 28), (cx + 36, cy - 32), (cx - 24, cy - 46), (cx + 28, cy - 50)]
        for i, (px, py) in enumerate(points[:max(2, show_confetti * 2)]):
            c = colors[i % len(colors)]
            draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=c)

    canvas.paste(cell, (cell_x, cell_y), cell)


def generate_hime_spritesheet(output_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    sheet = Image.new("RGBA", (SHEET_W, SHEET_H), (0, 0, 0, 0))

    # Row 0: Idle (6 frames)
    for col in range(6):
        hover = math.sin((col / 6.0) * 2 * math.pi) * 5
        tail = math.sin((col / 6.0) * 2 * math.pi)
        eye = "blink" if col in (2, 3) else "normal"
        draw_hime(sheet, col=col, row=0, hover_y=hover, eye_style=eye, tail_swing=tail)

    # Row 1: Walk (8 frames)
    for col in range(8):
        tilt = math.sin((col / 8.0) * 2 * math.pi) * 6
        hover = abs(math.sin((col / 8.0) * 2 * math.pi)) * -8
        tail = math.cos((col / 8.0) * 2 * math.pi) * 1.5
        draw_hime(sheet, col=col, row=1, hover_y=hover, tilt_x=tilt, tail_swing=tail, hand_left=(-24, 20 + int(tilt)), hand_right=(24, 20 - int(tilt)))

    # Row 2: Work (8 frames)
    for col in range(8):
        hl_y = 14 if (col % 2 == 0) else 20
        hr_y = 20 if (col % 2 == 0) else 14
        draw_hime(sheet, col=col, row=2, hover_y=-2, hand_left=(-12, hl_y), hand_right=(12, hr_y), show_laptop=True)

    # Row 3: Sleep (4 frames)
    for col in range(4):
        hover = 12 + math.sin((col / 4.0) * 2 * math.pi) * 2
        draw_hime(sheet, col=col, row=3, hover_y=hover, eye_style="sleep", tail_swing=-1.0, show_zzz=(col % 3) + 1)

    # Row 4: Wake (5 frames)
    for col in range(5):
        hover = 10 - col * 3
        eye = "sleep" if col < 2 else ("blink" if col == 2 else "normal")
        draw_hime(sheet, col=col, row=4, hover_y=hover, eye_style=eye)

    # Row 5: Play (8 frames)
    for col in range(8):
        angle = (col / 8.0) * 2 * math.pi
        hover = -14 + math.sin(angle) * 6
        tail = math.sin(angle) * 2
        draw_hime(sheet, col=col, row=5, hover_y=hover, eye_style="happy", tail_swing=tail, hand_left=(-26 + math.cos(angle) * 8, 12 + math.sin(angle) * 8), hand_right=(26 - math.cos(angle) * 8, 12 - math.sin(angle) * 8))

    # Row 6: Happy (6 frames)
    for col in range(6):
        hover = -6 + (col % 2) * -6
        tail = (col % 2) * 1.5
        draw_hime(sheet, col=col, row=6, hover_y=hover, eye_style="happy", tail_swing=tail, show_hearts=True)

    # Row 7: Curious (6 frames)
    for col in range(6):
        tilt = 5 if col >= 2 else 0
        draw_hime(sheet, col=col, row=7, hover_y=0, tilt_x=tilt, eye_style="curious")

    # Row 8: Celebrate (6 frames)
    for col in range(6):
        hover = -12 + math.sin((col / 6.0) * 2 * math.pi) * 5
        tail = math.sin((col / 6.0) * 2 * math.pi) * 2
        draw_hime(sheet, col=col, row=8, hover_y=hover, eye_style="happy", tail_swing=tail, hand_left=(-22, -10), hand_right=(22, -10), show_confetti=min(2, col + 1), show_sakura=True)

    sheet.save(output_path, "PNG")
    print(f"Generated Hime spritesheet at: {output_path}")

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "assets", "hime_pet.png")
    generate_hime_spritesheet(out)
