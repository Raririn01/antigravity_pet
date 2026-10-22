"""
Generates a complete, high-quality default Desktop Pet sprite sheet
conforming strictly to ChatGPT Pet v1 specification:
- Dimensions: 1536 x 1872 px (8 columns x 9 rows)
- Cell Size: 192 x 208 px
- Transparent background (RGBA)
- Exact frame counts per row: [6, 8, 8, 4, 5, 8, 6, 6, 6]
"""

import math
from PIL import Image, ImageDraw, ImageFont
import os

CELL_W = 192
CELL_H = 208
COLS = 8
ROWS = 9
SHEET_W = 1536
SHEET_H = 1872

FRAME_COUNTS = [6, 8, 8, 4, 5, 8, 6, 6, 6]


def draw_cat_ears(draw: ImageDraw.ImageDraw, cx: int, cy: int, ear_tilt: float = 0):
    # Left ear
    draw.polygon(
        [(cx - 32, cy - 25), (cx - 48, cy - 56), (cx - 16, cy - 38)],
        fill=(56, 189, 248, 255),
        outline=(14, 116, 144, 255)
    )
    # Inner left ear
    draw.polygon(
        [(cx - 30, cy - 28), (cx - 42, cy - 50), (cx - 20, cy - 36)],
        fill=(244, 114, 182, 255)
    )

    # Right ear
    draw.polygon(
        [(cx + 32, cy - 25), (cx + 48, cy - 56), (cx + 16, cy - 38)],
        fill=(56, 189, 248, 255),
        outline=(14, 116, 144, 255)
    )
    # Inner right ear
    draw.polygon(
        [(cx + 30, cy - 28), (cx + 42, cy - 50), (cx + 20, cy - 36)],
        fill=(244, 114, 182, 255)
    )


def draw_pet(
    canvas: Image.Image,
    col: int,
    row: int,
    hover_y: float = 0,
    eye_style: str = "normal",  # normal, blink, happy, sleep, wide, look_side
    mouth_style: str = "smile",  # smile, open, small, flat
    hand_left: tuple = (-35, 15),
    hand_right: tuple = (35, 15),
    show_laptop: bool = False,
    show_zzz: int = 0,  # 1, 2, 3
    show_hearts: bool = False,
    show_question: bool = False,
    show_confetti: int = 0,  # 1, 2, 3
    show_antenna_flash: bool = False,
    tilt_body_x: float = 0,
):
    cell_x = col * CELL_W
    cell_y = row * CELL_H
    
    # We create a temporary cell RGBA image
    cell = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(cell)
    
    cx = CELL_W // 2 + int(tilt_body_x)
    cy = CELL_H // 2 + 10 + int(hover_y)
    
    # --- Shadow on the ground ---
    shadow_scale = max(0.5, 1.0 - (hover_y / 30.0))
    sw = int(45 * shadow_scale)
    sh = int(12 * shadow_scale)
    shadow_y = CELL_H - 26
    draw.ellipse(
        [CELL_W // 2 - sw, shadow_y - sh, CELL_W // 2 + sw, shadow_y + sh],
        fill=(30, 41, 59, 70)
    )
    
    # --- Thruster Glow (under body) ---
    thrust_h = max(4, int(10 + hover_y * 0.5))
    draw.ellipse(
        [cx - 16, cy + 30, cx + 16, cy + 30 + thrust_h],
        fill=(56, 189, 248, 160)
    )
    draw.ellipse(
        [cx - 8, cy + 30, cx + 8, cy + 30 + (thrust_h // 2)],
        fill=(255, 255, 255, 220)
    )

    # --- Antenna / Ears ---
    draw_cat_ears(draw, cx, cy)
    
    # Antenna rod
    draw.line([(cx, cy - 35), (cx, cy - 54)], fill=(14, 116, 144, 255), width=3)
    # Antenna bulb
    bulb_color = (250, 204, 21, 255) if show_antenna_flash else (56, 189, 248, 255)
    draw.ellipse([cx - 7, cy - 64, cx + 7, cy - 50], fill=bulb_color, outline=(14, 116, 144, 255), width=2)
    if show_antenna_flash:
        # Glow ring
        draw.ellipse([cx - 12, cy - 69, cx + 12, cy - 45], outline=(253, 224, 71, 180), width=2)

    # --- Main Head/Body (Cute rounded blob) ---
    bw, bh = 46, 38
    # Outer stroke / body
    draw.rounded_rectangle(
        [cx - bw, cy - bh, cx + bw, cy + bh],
        radius=26,
        fill=(248, 250, 252, 255),
        outline=(14, 116, 144, 255),
        width=3
    )
    
    # --- Visor / Face Screen ---
    vw, vh = 36, 23
    draw.rounded_rectangle(
        [cx - vw, cy - vh + 2, cx + vw, cy + vh + 2],
        radius=14,
        fill=(15, 23, 42, 255),
        outline=(56, 189, 248, 200),
        width=2
    )

    # --- Eyes (Cyan glowing LED) ---
    eye_col = (56, 189, 248, 255)
    lx, rx = cx - 16, cx + 16
    ey = cy + 2
    
    if eye_style == "blink":
        # Closed horizontal slit
        draw.line([(lx - 7, ey), (lx + 7, ey)], fill=eye_col, width=3)
        draw.line([(rx - 7, ey), (rx + 7, ey)], fill=eye_col, width=3)
    elif eye_style == "happy":
        # Happy curves ( ^ ^ )
        draw.arc([lx - 8, ey - 6, lx + 8, ey + 6], 200, 340, fill=eye_col, width=3)
        draw.arc([rx - 8, ey - 6, rx + 8, ey + 6], 200, 340, fill=eye_col, width=3)
        # Rosy Cheeks
        draw.ellipse([lx - 15, ey + 7, lx - 7, ey + 13], fill=(244, 114, 182, 180))
        draw.ellipse([rx + 7, ey + 7, rx + 15, ey + 13], fill=(244, 114, 182, 180))
    elif eye_style == "sleep":
        # Sleeping horizontal curves ( - - )
        draw.line([(lx - 8, ey), (lx + 8, ey)], fill=(148, 163, 184, 255), width=2)
        draw.line([(rx - 8, ey), (rx + 8, ey)], fill=(148, 163, 184, 255), width=2)
    elif eye_style == "wide":
        # Big curious circles ( O O )
        draw.ellipse([lx - 8, ey - 8, lx + 8, ey + 8], fill=eye_col)
        draw.ellipse([rx - 8, ey - 8, rx + 8, ey + 8], fill=eye_col)
        # Pupils / reflection
        draw.ellipse([lx - 2, ey - 4, lx + 4, ey + 2], fill=(255, 255, 255, 255))
        draw.ellipse([rx - 2, ey - 4, rx + 4, ey + 2], fill=(255, 255, 255, 255))
    elif eye_style == "look_side":
        # Look sideways
        draw.ellipse([lx - 5 + 4, ey - 6, lx + 7 + 4, ey + 6], fill=eye_col)
        draw.ellipse([rx - 5 + 4, ey - 6, rx + 7 + 4, ey + 6], fill=eye_col)
    else:  # normal
        draw.ellipse([lx - 6, ey - 7, lx + 6, ey + 7], fill=eye_col)
        draw.ellipse([rx - 6, ey - 7, rx + 6, ey + 7], fill=eye_col)
        # Highlight sparkle
        draw.ellipse([lx - 2, ey - 4, lx + 3, ey + 1], fill=(255, 255, 255, 255))
        draw.ellipse([rx - 2, ey - 4, rx + 3, ey + 1], fill=(255, 255, 255, 255))

    # --- Mouth ---
    my = cy + 13
    if mouth_style == "smile":
        draw.arc([cx - 6, my - 4, cx + 6, my + 4], 20, 160, fill=eye_col, width=2)
    elif mouth_style == "open":
        draw.ellipse([cx - 4, my - 3, cx + 4, my + 5], fill=eye_col)
    elif mouth_style == "cat":
        # :3 shape
        draw.arc([cx - 6, my - 2, cx, my + 4], 20, 160, fill=eye_col, width=2)
        draw.arc([cx, my - 2, cx + 6, my + 4], 20, 160, fill=eye_col, width=2)

    # --- Hands / Paws ---
    hlx, hly = cx + hand_left[0], cy + hand_left[1]
    hrx, hry = cx + hand_right[0], cy + hand_right[1]
    
    # Left hand
    draw.ellipse([hlx - 9, hly - 9, hlx + 9, hly + 9], fill=(241, 245, 249, 255), outline=(14, 116, 144, 255), width=2)
    # Right hand
    draw.ellipse([hrx - 9, hry - 9, hrx + 9, hry + 9], fill=(241, 245, 249, 255), outline=(14, 116, 144, 255), width=2)

    # --- Extra Props ---
    if show_laptop:
        # Cute holographic mini laptop
        lap_x = cx - 22
        lap_y = cy + 18
        # Keyboard base
        draw.polygon([(lap_x, lap_y + 16), (lap_x + 44, lap_y + 16), (lap_x + 36, lap_y + 6), (lap_x + 8, lap_y + 6)], fill=(51, 65, 85, 255))
        # Screen
        draw.polygon([(lap_x + 6, lap_y + 5), (lap_x + 38, lap_y + 5), (lap_x + 38, lap_y - 18), (lap_x + 6, lap_y - 18)], fill=(30, 41, 59, 255), outline=(56, 189, 248, 255), width=1)
        # Screen glow code lines
        draw.line([(lap_x + 10, lap_y - 13), (lap_x + 28, lap_y - 13)], fill=(56, 189, 248, 255), width=2)
        draw.line([(lap_x + 10, lap_y - 8), (lap_x + 34, lap_y - 8)], fill=(74, 222, 128, 255), width=2)
        draw.line([(lap_x + 10, lap_y - 3), (lap_x + 22, lap_y - 3)], fill=(244, 114, 182, 255), width=2)

    if show_zzz > 0:
        # Floating Zzz
        zs = ["z", "Z", "Z"]
        for idx in range(show_zzz):
            zx = cx + 24 + idx * 10
            zy = cy - 20 - idx * 14
            # Draw Z manually with clean lines
            draw.line([(zx, zy), (zx + 8 + idx * 2, zy)], fill=(148, 163, 184, 220), width=2)
            draw.line([(zx + 8 + idx * 2, zy), (zx, zy + 8 + idx * 2)], fill=(148, 163, 184, 220), width=2)
            draw.line([(zx, zy + 8 + idx * 2), (zx + 8 + idx * 2, zy + 8 + idx * 2)], fill=(148, 163, 184, 220), width=2)

    if show_hearts:
        # Cute pink floating heart
        hx = cx + 32
        hy = cy - 25
        draw.polygon([(hx, hy + 12), (hx - 9, hy + 2), (hx - 9, hy - 6), (hx - 3, hy - 10), (hx, hy - 5), (hx + 3, hy - 10), (hx + 9, hy - 6), (hx + 9, hy + 2)], fill=(244, 114, 182, 255))

    if show_question:
        # Cute glowing question mark
        qx = cx + 32
        qy = cy - 28
        draw.arc([qx - 6, qy - 12, qx + 6, qy], 180, 360, fill=(250, 204, 21, 255), width=3)
        draw.line([(qx + 6, qy - 6), (qx, qy + 4)], fill=(250, 204, 21, 255), width=3)
        draw.ellipse([qx - 2, qy + 9, qx + 2, qy + 13], fill=(250, 204, 21, 255))

    if show_confetti > 0:
        # Confetti stars & sparkles
        colors = [(250, 204, 21, 255), (244, 114, 182, 255), (56, 189, 248, 255), (74, 222, 128, 255)]
        points = [
            (cx - 40, cy - 30), (cx + 42, cy - 35), (cx - 28, cy - 50),
            (cx + 30, cy - 55), (cx - 48, cy - 10), (cx + 46, cy - 10)
        ]
        for i, (px, py) in enumerate(points[:show_confetti * 2]):
            c = colors[i % len(colors)]
            draw.line([(px - 3, py), (px + 3, py)], fill=c, width=2)
            draw.line([(px, py - 3), (px, py + 3)], fill=c, width=2)

    # Paste cell into overall sprite sheet
    canvas.paste(cell, (cell_x, cell_y), cell)


def generate_pet_spritesheet(output_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    sheet = Image.new("RGBA", (SHEET_W, SHEET_H), (0, 0, 0, 0))

    # --- ROW 0: IDLE (6 frames) ---
    # Hovering gently up and down, blinking occasionally
    for col in range(6):
        hover = math.sin((col / 6.0) * 2 * math.pi) * 6
        eye = "blink" if col in (2, 3) else "normal"
        draw_pet(sheet, col=col, row=0, hover_y=hover, eye_style=eye, mouth_style="smile")

    # --- ROW 1: WALK / MOVE (8 frames) ---
    # Bobbing side to side, tilted, active thrusters
    for col in range(8):
        tilt = math.sin((col / 8.0) * 2 * math.pi) * 8
        hover = abs(math.sin((col / 8.0) * 2 * math.pi)) * -10
        hl = (-35, 15 + int(tilt * 0.8))
        hr = (35, 15 - int(tilt * 0.8))
        draw_pet(sheet, col=col, row=1, hover_y=hover, tilt_body_x=tilt, eye_style="normal", hand_left=hl, hand_right=hr)

    # --- ROW 2: WORK / TYPING (8 frames) ---
    # Rapid typing on holographic laptop, concentrated eyes
    for col in range(8):
        hover = -3 + (col % 2) * 2
        hl_y = 10 if (col % 2 == 0) else 18
        hr_y = 18 if (col % 2 == 0) else 10
        draw_pet(
            sheet, col=col, row=2, hover_y=hover, eye_style="normal",
            hand_left=(-16, hl_y), hand_right=(16, hr_y), show_laptop=True
        )

    # --- ROW 3: SLEEP (4 frames) ---
    # Floating low, eyes closed, floating Zzz bubbles
    for col in range(4):
        hover = 16 + math.sin((col / 4.0) * 2 * math.pi) * 3
        draw_pet(
            sheet, col=col, row=3, hover_y=hover, eye_style="sleep",
            mouth_style="flat", show_zzz=(col % 3) + 1
        )

    # --- ROW 4: WAKE UP / ALERT (5 frames) ---
    # Rising up, yawning, eyes opening wide, antenna lighting up!
    for col in range(5):
        hover = 12 - col * 4
        if col < 2:
            eye, mouth = "sleep", "open"
        elif col == 2:
            eye, mouth = "blink", "open"
        else:
            eye, mouth = "wide", "smile"
        draw_pet(
            sheet, col=col, row=4, hover_y=hover, eye_style=eye,
            mouth_style=mouth, show_antenna_flash=(col >= 3)
        )

    # --- ROW 5: PLAY / INTERACTIVE (8 frames) ---
    # Bouncing up high, juggling hands, rotating joyfully
    for col in range(8):
        angle = (col / 8.0) * 2 * math.pi
        hover = -18 + math.sin(angle) * 8
        hl = (-38 + math.cos(angle) * 12, 5 + math.sin(angle) * 12)
        hr = (38 - math.cos(angle) * 12, 5 - math.sin(angle) * 12)
        draw_pet(
            sheet, col=col, row=5, hover_y=hover, eye_style="happy",
            mouth_style="cat", hand_left=hl, hand_right=hr
        )

    # --- ROW 6: HAPPY / LOVE (6 frames) ---
    # Bouncing with blushing cheeks and floating hearts
    for col in range(6):
        hover = -8 + (col % 2) * -8
        draw_pet(
            sheet, col=col, row=6, hover_y=hover, eye_style="happy",
            mouth_style="smile", show_hearts=True,
            hand_left=(-32, 5), hand_right=(32, 5)
        )

    # --- ROW 7: CURIOUS / CONFUSED (6 frames) ---
    # Tilting head, question mark floating, looking around
    for col in range(6):
        tilt = 6 if col >= 2 else 0
        eye = "look_side" if col in (1, 2, 3) else "wide"
        draw_pet(
            sheet, col=col, row=7, hover_y=0, tilt_body_x=tilt,
            eye_style=eye, mouth_style="small", show_question=(col >= 2)
        )

    # --- ROW 8: CELEBRATE / VICTORY (6 frames) ---
    # Hands high in the air, stars and confetti explosion!
    for col in range(6):
        hover = -14 + math.sin((col / 6.0) * 2 * math.pi) * 6
        hl = (-30, -18)
        hr = (30, -18)
        draw_pet(
            sheet, col=col, row=8, hover_y=hover, eye_style="happy",
            mouth_style="open", hand_left=hl, hand_right=hr,
            show_confetti=min(3, col + 1), show_antenna_flash=True
        )

    sheet.save(output_path, "PNG")
    print(f"Generated default pet spritesheet at: {output_path}")


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "assets", "default_pet.png")
    generate_pet_spritesheet(out)
