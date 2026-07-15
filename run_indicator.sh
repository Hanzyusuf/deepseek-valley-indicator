#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export DISPLAY=${DISPLAY:-:0}
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}

LOG_DIR="$HOME/.cache/valley-indicator"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/indicator.log"
PID_FILE="$LOG_DIR/indicator.pid"
LOCK_FILE="$HOME/.valley_indicator.lock"

cd "$SCRIPT_DIR"

# Function to check if already running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            return 0  # Running
        else
            # Stale PID file
            rm -f "$PID_FILE"
            rm -f "$LOCK_FILE"
            return 1  # Not running
        fi
    fi
    return 1  # Not running
}

# Check if running
if is_running; then
    PID=$(cat "$PID_FILE")
    echo "⚠️  Valley indicator is already running (PID: $PID)"
    echo ""
    echo "Options:"
    echo "  1. Keep it running"
    echo "  2. Restart (kill and start new)"
    echo "  3. Stop it"
    echo "  4. Exit"
    read -p "Choose an option (1-4): " choice
    
    case $choice in
        2)
            echo "Restarting..."
            kill $PID
            rm -f "$PID_FILE" "$LOCK_FILE"
            sleep 1
            ;;
        3)
            echo "Stopping..."
            kill $PID
            rm -f "$PID_FILE" "$LOCK_FILE"
            echo "Stopped"
            exit 0
            ;;
        4)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Keeping existing instance running..."
            exit 0
            ;;
    esac
fi

# Start new instance
echo "========================================" >> "$LOG_FILE"
echo "Starting valley indicator at $(date)" >> "$LOG_FILE"
echo "Display: $DISPLAY" >> "$LOG_FILE"

# Run in background
nohup python3 "$SCRIPT_DIR/valley_indicator.py" >> "$LOG_FILE" 2>&1 &

# Save PID
echo $! > "$PID_FILE"
echo "Started with PID: $!" >> "$LOG_FILE"

echo "✅ Valley indicator started (PID: $!)"
echo "📝 Logs: $LOG_FILE"