"""
Sprite sheet parser and validator for Desktop Pet.
Fully compatible with ChatGPT Pet sprite sheet specifications:
- Cell Size: 192 x 208 pixels
- v1 Grid: 1536 x 1872 (8 columns x 9 rows)
  Row 0: idle (6 frames) - calm, visibly alive loop (matches resting pose)
  Row 1: running-right (8 frames) - directional movement right
  Row 2: running-left (8 frames) - directional movement left
  Row 3: waving (4 frames) - greeting / wave
  Row 4: jumping (5 frames) - jump / excitement
  Row 5: failed (8 frames) - failure reaction
  Row 6: waiting (6 frames) - expectant request for approval / input
  Row 7: thinking (6 frames) - active work, processing, thinking, focused effort
  Row 8: review (6 frames) - celebrate / inspecting completed work
- v2 Grid: 1536 x 2288 (8 columns x 11 rows)
  Row 9: look-1 (8 frames) - directions 000 through 157.5
  Row 10: look-2 (8 frames) - directions 180 through 337.5
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from PIL import Image

CELL_WIDTH = 192
CELL_HEIGHT = 208
COLUMNS = 8

ROW_FRAME_COUNTS_V1 = [6, 8, 8, 4, 5, 8, 6, 6, 6]
ROW_FRAME_COUNTS_V2 = [6, 8, 8, 4, 5, 8, 6, 6, 6, 8, 8]

ACTION_NAMES_V1 = [
    "idle",          # Row 0
    "running-right",  # Row 1
    "running-left",   # Row 2
    "waving",         # Row 3
    "jumping",        # Row 4
    "failed",         # Row 5
    "waiting",        # Row 6
    "thinking",       # Row 7 (active work, processing, thinking -> Image 2)
    "review",         # Row 8 (celebrate / inspect)
]

ACTION_NAMES_V2 = ACTION_NAMES_V1 + ["look-1", "look-2"]

ACTION_ALIASES = {
    "work": "thinking",
    "running": "thinking",
    "thinking": "thinking",
    "curious": "thinking",
    "celebrate": "review",
    "done": "review",
    "ready": "review",
    "review": "review",
    "happy": "waving",
    "wave": "waving",
    "wake": "waving",
    "play": "jumping",
    "jump": "jumping",
    "sleep": "waiting",
    "waiting": "waiting",
    "needs_input": "waiting",
    "needs input": "waiting",
    "blocked": "failed",
    "failed": "failed",
    "error": "failed",
    "walk": "running-right",
    "run": "running-right",
    "idle": "idle",
}


@dataclass
class ValidationResult:
    is_valid: bool
    version: Optional[str]
    errors: List[str]
    warnings: List[str]
    width: int
    height: int


def validate_spritesheet(image_path: str) -> ValidationResult:
    """Validates an image against the ChatGPT pet sprite-sheet spec."""
    errors = []
    warnings = []
    
    try:
        with Image.open(image_path) as img:
            w, h = img.size
            mode = img.mode
            
            if mode not in ("RGBA", "LA") and "transparency" not in img.info:
                errors.append(f"Image has mode '{mode}', but must have an alpha channel (transparency).")
            
            if (w, h) == (1536, 1872):
                version = "v1"
                expected_counts = ROW_FRAME_COUNTS_V1
            elif (w, h) == (1536, 2288):
                version = "v2"
                expected_counts = ROW_FRAME_COUNTS_V2
            else:
                errors.append(
                    f"Invalid dimensions {w}x{h}. Must be exactly 1536x1872 (v1) or 1536x2288 (v2)."
                )
                return ValidationResult(
                    is_valid=False,
                    version=None,
                    errors=errors,
                    warnings=warnings,
                    width=w,
                    height=h
                )
            
            rgba_img = img.convert("RGBA")
            rows = len(expected_counts)
            
            for r in range(rows):
                needed_frames = expected_counts[r]
                for c in range(COLUMNS):
                    box = (c * CELL_WIDTH, r * CELL_HEIGHT, (c + 1) * CELL_WIDTH, (r + 1) * CELL_HEIGHT)
                    cell = rgba_img.crop(box)
                    alpha_channel = cell.getchannel("A")
                    has_pixels = alpha_channel.getextrema()[1] > 0
                    
                    if c < needed_frames:
                        if not has_pixels:
                            warnings.append(f"Row {r} ({ACTION_NAMES_V1[r] if r < len(ACTION_NAMES_V1) else r}), Frame {c}: cell appears empty.")
                    else:
                        if has_pixels:
                            errors.append(f"Row {r}, Col {c} is an unused cell but contains non-transparent pixels.")
            
            return ValidationResult(
                is_valid=(len(errors) == 0),
                version=version,
                errors=errors,
                warnings=warnings,
                width=w,
                height=h
            )
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            version=None,
            errors=[f"Failed to open image: {str(e)}"],
            warnings=[],
            width=0,
            height=0
        )


class SpriteSheet:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.pil_image = Image.open(file_path).convert("RGBA")
        self.width, self.height = self.pil_image.size
        
        if (self.width, self.height) == (1536, 2288):
            self.version = "v2"
            self.frame_counts = ROW_FRAME_COUNTS_V2
            self.action_names = ACTION_NAMES_V2
        else:
            self.version = "v1"
            self.frame_counts = ROW_FRAME_COUNTS_V1
            self.action_names = ACTION_NAMES_V1
            
        self.frames: Dict[str, List[Image.Image]] = {}
        self._slice_frames()

    def _slice_frames(self):
        for r_idx, (action, count) in enumerate(zip(self.action_names, self.frame_counts)):
            action_frames = []
            for c_idx in range(count):
                x1 = c_idx * CELL_WIDTH
                y1 = r_idx * CELL_HEIGHT
                x2 = x1 + CELL_WIDTH
                y2 = y1 + CELL_HEIGHT
                frame = self.pil_image.crop((x1, y1, x2, y2))
                action_frames.append(frame)
            self.frames[action.lower()] = action_frames

    def get_action_frames(self, action_name: str) -> List[Image.Image]:
        key = action_name.lower().strip()
        canonical = ACTION_ALIASES.get(key, key)
        return self.frames.get(canonical, self.frames.get(key, self.frames.get("idle", [])))
