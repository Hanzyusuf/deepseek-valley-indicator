#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export DISPLAY=${DISPLAY:-:0}
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}

LOG_DIR="$HOME/.cache/valley-indicator"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/indicator.log"

cd "$SCRIPT_DIR"

# Remove old lock file
rm -f ~/.valley_indicator.lock

echo "========================================" >> "$LOG_FILE"
echo "Starting valley indicator at $(date)" >> "$LOG_FILE"
echo "Display: $DISPLAY" >> "$LOG_FILE"

# Run in background - NO daemon flag
nohup python3 "$SCRIPT_DIR/valley_indicator.py" >> "$LOG_FILE" 2>&1 &

# Save PID
echo $! > "$LOG_DIR/indicator.pid"
echo "Started with PID: $!" >> "$LOG_FILE"

echo "Valley indicator started in background (PID: $!)"
echo "Logs: $LOG_FILE"