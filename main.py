"""
Main launcher for Antigravity Desktop Pet.
"""

import os
import sys
import argparse
import ctypes

# Ensure GUI attaches to the interactive user desktop (WinSta0\Default)
if sys.platform == "win32":
    try:
        user32 = ctypes.windll.user32
        h_desk_default = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if h_desk_default:
            user32.SetThreadDesktop(h_desk_default)
    except Exception as e:
        print(f"Warning: could not switch desktop: {e}")

from PyQt6.QtWidgets import QApplication

from pet_window import DesktopPet
from default_pet_generator import generate_pet_spritesheet


def main():
    parser = argparse.ArgumentParser(description="Antigravity Desktop Pet")
    parser.add_argument("--pet", type=str, default=None, help="Path to custom pet sprite sheet PNG/WebP")
    parser.add_argument("--scale", type=float, default=0.75, help="Scale factor (default: 0.75)")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_asset = os.path.join(base_dir, "assets", "default_pet.png")

    # Ensure default pet asset exists
    if not os.path.exists(default_asset):
        print("Generating default pet sprite sheet...")
        generate_pet_spritesheet(default_asset)

    pet_path = args.pet if args.pet and os.path.exists(args.pet) else default_asset

    app = QApplication(sys.argv)
    app.setApplicationName("Antigravity Desktop Pet")

    pet = DesktopPet(pet_path)
    should_show = pet.restore_preferences()
    if args.scale != 0.75:
        pet.set_scale(args.scale)
    app.setQuitOnLastWindowClosed(False)
    pet.show()
    if not should_show:
        pet.hide()

    print("Antigravity Desktop Pet is running!")
    print("- Left Click & Drag: Move anywhere on desktop")
    print("- Left Click: Poke pet")
    print("- Double Click: Celebrate spin")
    print("- Right Click: Pet settings, open Antigravity, or hide")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
