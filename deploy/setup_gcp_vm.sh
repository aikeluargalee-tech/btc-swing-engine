#!/usr/bin/env bash
# ==============================================================================
# BTC SWING ENGINE - GOOGLE CLOUD VM PROVISIONING SCRIPT
# Target: Ubuntu 22.04 LTS / 24.04 LTS on GCP e2-micro (Always Free Tier)
# ==============================================================================
set -e

echo "======================================================================"
echo ">>> [1/6] STARTING GOOGLE CLOUD VM PROVISIONING FOR BTC SWING ENGINE"
echo "======================================================================"

# Step 1: Configure 2GB Swap Space
# The e2-micro provides 1GB of physical RAM. A 2GB swapfile guarantees
# that memory spikes during pip package installations or calculation bursts
# will never trigger the Linux OOM (Out Of Memory) killer.
if [ ! -f /swapfile ]; then
    echo ">>> Creating 2GB Swapfile on standard persistent disk..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo ">>> 2GB Swapfile active and registered in /etc/fstab."
else
    echo ">>> Swapfile already exists. Skipping creation."
fi

# Step 2: System updates and base package installation
echo ">>> [2/6] Updating APT repositories and installing dependencies..."
sudo apt update -y
sudo apt install -y python3-pip python3-venv git tmux curl jq htop

# Step 3: Set Timezone to UTC
echo ">>> [3/6] Setting system timezone to UTC..."
sudo timedatectl set-timezone UTC

# Step 4: Python Virtual Environment Setup
echo ">>> [4/6] Creating Python 3 Virtual Environment..."
cd "$(dirname "$0")/.."
INSTALL_DIR=$(pwd)
echo ">>> Working directory: $INSTALL_DIR"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo ">>> Virtual environment created in .venv"
fi

# Step 5: Install Python Dependencies
echo ">>> [5/6] Installing Python wheel and requirements..."
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Ensure log directory exists
mkdir -p logs

# Step 6: Test connectivity from Google Cloud Datacenter IP
echo ">>> [6/6] Verifying WebSocket & REST Connectivity from US Datacenter..."
python main.py --dry-run --duration 3 --tab p

echo "======================================================================"
echo ">>> PROVISIONING COMPLETE! ENGINE IS READY FOR 24/7 OPERATION."
echo "======================================================================"
echo ""
echo "Quick Commands:"
echo "  1. Start in tmux:          bash deploy/run_tmux.sh"
echo "  2. Attach to live HUD:     tmux attach -t btc_engine"
echo "  3. Detach from tmux:       Press Ctrl+B, then D"
echo "  4. Termius mobile hotkeys: [P] Structure, [F] Footprint, [W] Waterfall, [0] Screener, [L] Master, [C] AI Packet"
echo "======================================================================"
