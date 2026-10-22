#!/usr/bin/env python3
"""
Pet Tools CLI for Antigravity Desktop Pet.
Standard operations:
- validate: verify compliance with ChatGPT Pet v1 (1536x1872) and v2 (1536x2288) specs.
- preview: generate animated GIFs for each action.
- slice: extract individual frames by row and action.
- assemble: build standard spritesheet from organized frames.
"""

import sys
import os
import json
import argparse
from pathlib import Path
from PIL import Image
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

CELL_W = 192
CELL_H = 208
COLS = 8

V1_ROWS = 9
V2_ROWS = 11

V1_SIZE = (1536, 1872)
V2_SIZE = (1536, 2288)

ROW_CONFIG = [
    {"row": 0, "name": "idle", "frames": 6, "desc": "Calm, alive breathing loop"},
    {"row": 1, "name": "running-right", "frames": 8, "desc": "Running / moving right"},
    {"row": 2, "name": "running-left", "frames": 8, "desc": "Running / moving left"},
    {"row": 3, "name": "waving", "frames": 4, "desc": "Greeting / wave"},
    {"row": 4, "name": "jumping", "frames": 5, "desc": "Jump / excitement / play"},
    {"row": 5, "name": "failed", "frames": 8, "desc": "Error / sadness / failed reaction"},
    {"row": 6, "name": "waiting", "frames": 6, "desc": "Waiting / expectant / approval"},
    {"row": 7, "name": "thinking", "frames": 6, "desc": "Active work / computing / thinking"},
    {"row": 8, "name": "review", "frames": 6, "desc": "Celebration / inspect work / done"},
    {"row": 9, "name": "look-1", "frames": 8, "desc": "Gaze tracking: 0 to 157.5 deg (v2)"},
    {"row": 10, "name": "look-2", "frames": 8, "desc": "Gaze tracking: 180 to 337.5 deg (v2)"},
]


def validate_sheet(sheet_path: str) -> dict:
    p = Path(sheet_path)
    if not p.is_file():
        return {"valid": False, "errors": [f"File not found: {sheet_path}"], "warnings": []}

    try:
        img = Image.open(p)
    except Exception as exc:
        return {"valid": False, "errors": [f"Cannot open image: {exc}"], "warnings": []}

    errors = []
    warnings = []
    width, height = img.size

    version = None
    if (width, height) == V1_SIZE:
        version = "v1"
        expected_rows = V1_ROWS
    elif (width, height) == V2_SIZE:
        version = "v2"
        expected_rows = V2_ROWS
    else:
        errors.append(
            f"Invalid dimensions: {width}x{height}. Expected v1 ({V1_SIZE[0]}x{V1_SIZE[1]}) or v2 ({V2_SIZE[0]}x{V2_SIZE[1]})."
        )
        expected_rows = height // CELL_H

    if img.mode != "RGBA":
        errors.append(f"Invalid mode: {img.mode}. Must be RGBA with transparency.")

    row_details = []
    for cfg in ROW_CONFIG[:expected_rows]:
        r = cfg["row"]
        expected_frames = cfg["frames"]
        name = cfg["name"]

        actual_frames = 0
        blank_frames = []
        for c in range(COLS):
            box = (c * CELL_W, r * CELL_H, (c + 1) * CELL_W, (r + 1) * CELL_H)
            cell = img.crop(box)
            bbox = cell.getbbox()
            if bbox:
                actual_frames += 1
            else:
                blank_frames.append(c)

        status = "ok"
        if actual_frames < expected_frames:
            status = "missing_frames"
            errors.append(f"Row {r} ({name}): Expected {expected_frames} frames, found {actual_frames}.")
        elif actual_frames > expected_frames:
            # Not necessarily error, but warning
            warnings.append(f"Row {r} ({name}): Has {actual_frames} frames (spec expects {expected_frames}).")

        row_details.append({
            "row": r,
            "name": name,
            "expected_frames": expected_frames,
            "actual_frames": actual_frames,
            "status": status
        })

    is_valid = len(errors) == 0
    return {
        "valid": is_valid,
        "version": version,
        "dimensions": [width, height],
        "rows_checked": expected_rows,
        "errors": errors,
        "warnings": warnings,
        "row_details": row_details
    }


def benchmark_sheet(sheet_path: str) -> dict:
    """Evaluates spritesheet stability and precision against the Hime Gold Standard."""
    val = validate_sheet(sheet_path)
    if not val["valid"]:
        return {"score": 0, "tier": "Invalid", "error": val["errors"]}

    img = Image.open(sheet_path).convert("RGBA")
    total_rows = img.height // CELL_H

    # 1. Baseline analysis on grounded rows
    grounded_rows = [0, 3, 5, 6, 7, 8]
    if total_rows >= 11:
        grounded_rows.extend([9, 10])

    grounded_y2 = []
    x_centers = []
    white_halo_pixels = 0
    total_opaque_pixels = 0

    for r in range(total_rows):
        cfg = ROW_CONFIG[r] if r < len(ROW_CONFIG) else {"frames": 8}
        for c in range(cfg["frames"]):
            box = (c * CELL_W, r * CELL_H, (c + 1) * CELL_W, (r + 1) * CELL_H)
            cell = img.crop(box)
            bbox = cell.getbbox()
            if not bbox:
                continue

            # Foot Y
            if r in grounded_rows:
                grounded_y2.append(bbox[3])

            # X-Center in idle and gaze
            if r in (0, 9, 10):
                x_center = (bbox[0] + bbox[2]) / 2.0
                x_centers.append(x_center)

            # Fringe test for white halo (sample borders)
            arr = np.array(cell)
            r_c, g_c, b_c, a_c = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
            opaque = a_c > 0
            total_opaque_pixels += int(np.sum(opaque))
            halo_mask = (a_c > 5) & (a_c < 80) & (r_c > 240) & (g_c > 240) & (b_c > 240)
            white_halo_pixels += int(np.sum(halo_mask))

    # Baseline variance
    min_y2 = min(grounded_y2) if grounded_y2 else 203
    max_y2 = max(grounded_y2) if grounded_y2 else 203
    baseline_spread = max_y2 - min_y2

    # Center variance from 96.0
    avg_center = sum(x_centers) / len(x_centers) if x_centers else 96.0
    center_offset = abs(avg_center - 96.0)

    # Score calculation
    # Baseline jitter penalty: 0px=40pts, 1px=38pts, 2px=32pts, >5px=0pts
    baseline_score = max(0, 40 - (baseline_spread * 6))
    
    # Center balance penalty: <=1.0px is sub-pixel perfect (30pts)
    center_score = 30 if center_offset <= 1.0 else max(0, 30 - int((center_offset - 1.0) * 10))

    # Gaze completeness: v2 with rows 9&10 gets 20pts, v1 gets 10pts
    gaze_score = 20 if total_rows >= 11 else 10

    # Halo cleanliness: 10pts
    halo_ratio = (white_halo_pixels / total_opaque_pixels) if total_opaque_pixels else 0
    halo_score = 10 if halo_ratio < 0.005 else max(0, 10 - int(halo_ratio * 1000))

    total_score = int(baseline_score + center_score + gaze_score + halo_score)
    if total_score >= 95:
        tier = "S-Tier (Hime Gold Standard)"
    elif total_score >= 85:
        tier = "A-Tier (High Quality)"
    elif total_score >= 70:
        tier = "B-Tier (Passable)"
    else:
        tier = "C-Tier (Needs Normalization)"

    return {
        "score": total_score,
        "tier": tier,
        "spec_version": val["version"],
        "baseline_spread_px": baseline_spread,
        "min_feet_y": min_y2,
        "max_feet_y": max_y2,
        "avg_x_center": round(avg_center, 2),
        "center_offset_px": round(center_offset, 2),
        "white_halo_ratio": round(halo_ratio, 5),
        "breakdown": {
            "baseline_stability": f"{int(baseline_score)}/40",
            "horizontal_balance": f"{int(center_score)}/30",
            "gaze_completeness": f"{int(gaze_score)}/20",
            "alpha_cleanliness": f"{int(halo_score)}/10"
        }
    }


def slice_sheet(sheet_path: str, output_dir: str):
    p = Path(sheet_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    img = Image.open(p).convert("RGBA")
    total_rows = img.height // CELL_H

    saved = 0
    for r in range(total_rows):
        cfg = ROW_CONFIG[r] if r < len(ROW_CONFIG) else {"name": f"row_{r}", "frames": 8}
        row_name = cfg["name"]
        row_dir = out / f"{r:02d}_{row_name}"
        row_dir.mkdir(parents=True, exist_ok=True)

        for c in range(COLS):
            box = (c * CELL_W, r * CELL_H, (c + 1) * CELL_W, (r + 1) * CELL_H)
            cell = img.crop(box)
            if cell.getbbox():
                cell_path = row_dir / f"frame_{c:02d}.png"
                cell.save(cell_path, "PNG")
                saved += 1

    print(f"Sliced {saved} frames into {out}")
    return saved


def generate_previews(sheet_path: str, output_dir: str, duration_ms: int = 125):
    p = Path(sheet_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    img = Image.open(p).convert("RGBA")
    total_rows = img.height // CELL_H

    generated = []
    for r in range(total_rows):
        cfg = ROW_CONFIG[r] if r < len(ROW_CONFIG) else {"name": f"row_{r}", "frames": 8}
        name = cfg["name"]
        max_f = cfg.get("frames", 8)

        frames = []
        for c in range(max_f):
            box = (c * CELL_W, r * CELL_H, (c + 1) * CELL_W, (r + 1) * CELL_H)
            cell = img.crop(box)
            if cell.getbbox():
                frames.append(cell)

        if len(frames) > 1:
            gif_path = out / f"{r:02d}_{name}.gif"
            # Convert to palette with transparency preserved
            first = frames[0].convert("P", palette=Image.Palette.ADAPTIVE, colors=255)
            rest = [f.convert("P", palette=Image.Palette.ADAPTIVE, colors=255) for f in frames[1:]]
            first.save(
                gif_path,
                save_all=True,
                append_images=rest,
                duration=duration_ms,
                loop=0,
                disposal=2
            )
            generated.append(str(gif_path))

    print(f"Generated {len(generated)} animation previews in {out}")
    return generated


def assemble_sheet(frames_dir: str, output_path: str, version: str = "v2"):
    inp = Path(frames_dir)
    is_v2 = version.lower() == "v2"
    target_rows = V2_ROWS if is_v2 else V1_ROWS
    sheet_w, sheet_h = V2_SIZE if is_v2 else V1_SIZE

    canvas = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))

    # Expecting folders like 00_idle, 01_running-right or row_0, row_1
    subdirs = sorted([d for d in inp.iterdir() if d.is_dir()])
    placed = 0

    for r in range(target_rows):
        cfg = ROW_CONFIG[r]
        name = cfg["name"]
        matched_dir = None
        for d in subdirs:
            if d.name.startswith(f"{r:02d}") or d.name.startswith(f"row_{r}") or name in d.name:
                matched_dir = d
                break

        if not matched_dir:
            continue

        frame_files = sorted(list(matched_dir.glob("*.png")) + list(matched_dir.glob("*.webp")))
        for c, f_path in enumerate(frame_files[:COLS]):
            frame_img = Image.open(f_path).convert("RGBA")
            # Center if needed or fit in 192x208
            if frame_img.size != (CELL_W, CELL_H):
                # Resize or pad
                padded = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
                px = (CELL_W - frame_img.width) // 2
                py = CELL_H - frame_img.height  # align bottom
                padded.paste(frame_img, (px, py), frame_img)
                frame_img = padded

            canvas.paste(frame_img, (c * CELL_W, r * CELL_H), frame_img)
            placed += 1

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_file, "PNG")
    print(f"Assembled {placed} frames into {out_file} ({sheet_w}x{sheet_h})")
    return str(out_file)


def main():
    parser = argparse.ArgumentParser(description="Antigravity Desktop Pet Sprite Tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    val_p = subparsers.add_parser("validate", help="Validate spritesheet against v1/v2 spec")
    val_p.add_argument("path", help="Path to spritesheet image")
    val_p.add_argument("--json", action="store_true", help="Output JSON result")

    slice_p = subparsers.add_parser("slice", help="Slice sheet into row/frame folders")
    slice_p.add_argument("path", help="Path to spritesheet image")
    slice_p.add_argument("--out", default="./frames", help="Output directory")

    prev_p = subparsers.add_parser("preview", help="Generate animation preview GIFs")
    prev_p.add_argument("path", help="Path to spritesheet image")
    prev_p.add_argument("--out", default="./previews", help="Output directory")
    prev_p.add_argument("--fps", type=int, default=8, help="Frames per second")

    bench_p = subparsers.add_parser("benchmark", help="Benchmark stability and quality against Hime Gold Standard")
    bench_p.add_argument("path", help="Path to spritesheet image")
    bench_p.add_argument("--json", action="store_true", help="Output JSON result")

    ass_p = subparsers.add_parser("assemble", help="Assemble frames into standard spritesheet")
    ass_p.add_argument("frames_dir", help="Directory with frame folders")
    ass_p.add_argument("--out", required=True, help="Output PNG path")
    ass_p.add_argument("--version", choices=["v1", "v2"], default="v2", help="Spec version")

    args = parser.parse_args()

    if args.command == "validate":
        res = validate_sheet(args.path)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(f"--- Spritesheet Validation Report: {args.path} ---")
            print(f"Valid: {res['valid']} (Spec: {res.get('version', 'unknown')})")
            print(f"Dimensions: {res.get('dimensions')}")
            if res["errors"]:
                print("\nErrors:")
                for err in res["errors"]:
                    print(f"  ❌ {err}")
            if res["warnings"]:
                print("\nWarnings:")
                for w in res["warnings"]:
                    print(f"  ⚠️ {w}")
            if res["valid"]:
                print("\nAll required rows and frames passed validation! ✅")
        sys.exit(0 if res["valid"] else 1)

    elif args.command == "benchmark":
        res = benchmark_sheet(args.path)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(f"=== Pet Quality Benchmark (Hime Standard): {args.path} ===")
            print(f"Overall Score: {res.get('score', 0)}/100  -->  [{res.get('tier', 'Unknown')}]")
            print(f"Spec Version:  {res.get('spec_version', 'Unknown')}")
            print(f"Baseline Spread: {res.get('baseline_spread_px')}px (Target: <= 1px)  [Points: {res.get('breakdown', {}).get('baseline_stability')}]")
            print(f"Center Offset:   {res.get('center_offset_px')}px (Target: <= 1px)  [Points: {res.get('breakdown', {}).get('horizontal_balance')}]")
            print(f"Gaze Quality:    [Points: {res.get('breakdown', {}).get('gaze_completeness')}]")
            print(f"Alpha Fringe:    Halo ratio {res.get('white_halo_ratio')}  [Points: {res.get('breakdown', {}).get('alpha_cleanliness')}]")
            print("===========================================================")
        sys.exit(0 if res.get("score", 0) >= 85 else 1)

    elif args.command == "slice":
        slice_sheet(args.path, args.out)

    elif args.command == "preview":
        duration = int(1000 / args.fps)
        generate_previews(args.path, args.out, duration_ms=duration)

    elif args.command == "assemble":
        assemble_sheet(args.frames_dir, args.out, version=args.version)


if __name__ == "__main__":
    main()
