#!/usr/bin/env bash
# ==============================================================================
# BTC SWING ENGINE - TMUX PERSISTENT SESSION RUNNER
# Keeps the Live TUI HUD running continuously across SSH disconnects
# ==============================================================================

SESSION="btc_engine"
DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Check if session already exists
tmux has-session -t $SESSION 2>/dev/null

if [ $? != 0 ]; then
    echo ">>> Starting new persistent tmux session: $SESSION in $DIR..."
    # Launch new detached tmux session with UTF-8 and 256-color support
    tmux new-session -d -s $SESSION -c "$DIR" "export TERM=xterm-256color; export LANG=en_US.UTF-8; source .venv/bin/activate && python main.py --tab p"
    echo ">>> Session started successfully!"
fi

echo ">>> Attaching to session '$SESSION'..."
echo ">>> To detach without stopping the engine: Press Ctrl+B, then release and press D."
sleep 1
tmux attach-session -t $SESSION
