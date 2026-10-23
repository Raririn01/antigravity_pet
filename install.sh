#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "========================================================"
echo "  Installing Antigravity Desktop Pet Dependencies...   "
echo "========================================================"
echo ""

# Check python3
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is not installed or not in PATH!"
    echo "Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "CachyOS/Arch:  sudo pacman -S python python-pip"
    exit 1
fi

# Create virtual environment to comply with PEP 668
if [ ! -d "venv" ]; then
    echo "Creating virtual environment (venv)..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip and installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "========================================================"
echo "  [SUCCESS] Installed successfully!                    "
echo "  Launch the pet with: ./run_pet.sh                    "
echo "========================================================"
