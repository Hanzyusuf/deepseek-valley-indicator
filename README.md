# Valley Status Indicator - README

A lightweight system tray indicator for XFCE that shows time-based status (VALLEY/NORMAL) with timezone support.

## Features

- 🔴/🟢 Visual status indicator in system tray
- 🕐 Automatic timezone conversion
- 📅 12-hour time format
- ⏱️ Real-time remaining time display
- 🔄 Auto-updates every 30 seconds
- 🚀 Auto-starts on login
- ✏️ Edit schedule directly from menu

## Quick Installation

### 1. Clone or download files

```bash
# Create directory
mkdir -p ~/valley-indicator
cd ~/valley-indicator

# Download all files (or copy them manually)
# Files needed:
# - valley_indicator.py
# - scheduler.py
# - schedules.json
# - run_indicator.sh
# - install.sh
```

### 2. Run installation

```bash
chmod +x install.sh
./install.sh
```

### 3. Start the indicator

```bash
~/.local/share/valley-indicator/run_indicator.sh
```

### 4. Add to panel (if icon doesn't appear)

Right-click on panel → **Panel Preferences** → **Items** → **Add** → **Status Tray**

## Complete Installation Steps

### Option A: Using the installer (Recommended)

```bash
# 1. Create directory and copy files
mkdir -p ~/valley-indicator
cd ~/valley-indicator

# 2. Copy all files to this directory
# (valley_indicator.py, scheduler.py, schedules.json, 
#  run_indicator.sh, install.sh)

# 3. Make executable and install
chmod +x *.sh *.py
./install.sh

# 4. Start the indicator
~/.local/share/valley-indicator/run_indicator.sh
```

### Option B: Manual installation

```bash
# 1. Copy files to installation directory
mkdir -p ~/.local/share/valley-indicator
cp valley_indicator.py scheduler.py schedules.json run_indicator.sh ~/.local/share/valley-indicator/
chmod +x ~/.local/share/valley-indicator/*.py ~/.local/share/valley-indicator/*.sh

# 2. Create desktop entry for autostart
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/valley-indicator.desktop << 'EOF'
[Desktop Entry]
Name=Valley Status Indicator
Comment=Time-based status indicator for XFCE panel
Exec=/home/$USER/.local/share/valley-indicator/run_indicator.sh
Icon=applications-system
Terminal=false
Type=Application
StartupNotify=true
X-GNOME-Autostart-enabled=true
EOF

# 3. Enable autostart
mkdir -p ~/.config/autostart
cp ~/.local/share/applications/valley-indicator.desktop ~/.config/autostart/
```

## Usage

### Starting the indicator

```bash
# Start in background
~/.local/share/valley-indicator/run_indicator.sh

# Check if running
ps aux | grep valley_indicator.py
```

### Stopping the indicator

```bash
# Kill the process
pkill -f valley_indicator.py

# Or find and kill by PID
ps aux | grep valley_indicator.py
kill <PID>
```

### Restarting

```bash
# Stop and start
pkill -f valley_indicator.py && ~/.local/share/valley-indicator/run_indicator.sh
```

### Viewing logs

```bash
# View full log
cat ~/.cache/valley-indicator/indicator.log

# Follow log (live)
tail -f ~/.cache/valley-indicator/indicator.log

# View last 20 lines
tail -20 ~/.cache/valley-indicator/indicator.log
```

### Checking status

```bash
# Check if running
ps aux | grep valley_indicator.py | grep -v grep

# Check current status
~/.local/share/valley-indicator/scheduler.py
```

## How to Use

### Left-click on icon
Shows detailed status dialog with:
- Current state (VALLEY/NORMAL)
- Status message
- Remaining time
- Next window
- Timezone info
- Local time

### Right-click on icon
Menu options:
- **Show Details** - Same as left-click
- **Edit Schedule** - Opens `schedules.json` in default editor
- **Open Schedule Folder** - Opens folder containing schedule file
- **Refresh** - Manually update status
- **Quit** - Stop the indicator

### Hover over icon
Tooltip shows quick status information

## Configuration

### Editing schedules

1. Right-click the icon → **Edit Schedule**
2. Or edit manually:
```bash
nano ~/.local/share/valley-indicator/schedules.json
```

### Schedule format

```json
{
  "timezone": "America/New_York",
  "periods": [
    {
      "name": "VALLEY",
      "type": "peak",
      "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "start": "09:00 AM",
      "end": "10:30 AM",
      "message": "🔴 Peak hour - Avoid tokens"
    },
    {
      "name": "NORMAL",
      "type": "safe",
      "days": ["all"],
      "start": "12:00 AM",
      "end": "11:59 PM",
      "message": "🟢 Normal - Safe to proceed",
      "default": true
    }
  ]
}
```

### Available timezones

Common timezones:
- `America/New_York` (EST/EDT)
- `America/Chicago` (CST/CDT)
- `America/Denver` (MST/MDT)
- `America/Los_Angeles` (PST/PDT)
- `Europe/London` (GMT/BST)
- `Europe/Paris` (CET/CEST)
- `Asia/Kolkata` (IST)
- `Asia/Tokyo` (JST)
- `Australia/Sydney` (AEST/AEDT)
- `UTC` (Coordinated Universal Time)

## Reinstallation

```bash
# 1. Uninstall old version
rm -rf ~/.local/share/valley-indicator
rm -f ~/.valley_indicator.lock
rm -f ~/.local/share/applications/valley-indicator.desktop
rm -f ~/.config/autostart/valley-indicator.desktop
rm -rf ~/.cache/valley-indicator

# 2. Kill any running instances
pkill -f valley_indicator.py

# 3. Reinstall (follow installation steps above)
```

## Troubleshooting

### Icon doesn't appear

1. Add Status Tray to panel:
   - Right-click panel → **Panel Preferences** → **Items** → **Add** → **Status Tray**
   
2. Restart the panel:
```bash
xfce4-panel -r
```

3. Check if running:
```bash
ps aux | grep valley_indicator.py
```

### Indicator not updating

1. Check logs:
```bash
tail -f ~/.cache/valley-indicator/indicator.log
```

2. Manually refresh:
   - Right-click icon → **Refresh**

3. Restart the indicator:
```bash
pkill -f valley_indicator.py && ~/.local/share/valley-indicator/run_indicator.sh
```

### Permission errors

Make scripts executable:
```bash
chmod +x ~/.local/share/valley-indicator/*.py
chmod +x ~/.local/share/valley-indicator/*.sh
```

### Python errors

Check Python version (needs 3.9+):
```bash
python3 --version
```

Install missing dependencies:
```bash
sudo apt install python3 python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

## Files

| File | Location | Purpose |
|------|----------|---------|
| `valley_indicator.py` | `~/.local/share/valley-indicator/` | Main application |
| `scheduler.py` | `~/.local/share/valley-indicator/` | Status calculation |
| `schedules.json` | `~/.local/share/valley-indicator/` | Time period configuration |
| `run_indicator.sh` | `~/.local/share/valley-indicator/` | Launcher script |
| `valley-indicator.desktop` | `~/.local/share/applications/` | Desktop entry |
| `valley-indicator.desktop` | `~/.config/autostart/` | Autostart entry |
| `indicator.log` | `~/.cache/valley-indicator/` | Log file |

## Uninstallation

```bash
# 1. Stop the process
pkill -f valley_indicator.py

# 2. Remove all files
rm -rf ~/.local/share/valley-indicator
rm -f ~/.valley_indicator.lock
rm -f ~/.local/share/applications/valley-indicator.desktop
rm -f ~/.config/autostart/valley-indicator.desktop
rm -rf ~/.cache/valley-indicator

# 3. (Optional) Remove from panel
# Right-click panel → Panel Preferences → Items → Remove Status Tray
```

## Notes

- The indicator automatically starts on login
- Updates every 30 seconds
- Uses Python's built-in `zoneinfo` (Python 3.9+)
- No external Python packages required
- Lightweight (~15-25 MB RAM)

## Support

For issues:
1. Check logs: `tail -f ~/.cache/valley-indicator/indicator.log`
2. Check if running: `ps aux | grep valley_indicator.py`
3. Verify schedule: `~/.local/share/valley-indicator/scheduler.py`

## Save this as README.md in your project folder:

```bash
cd ~/valley-indicator
nano README.md
# Paste the above content
```

Now you have complete documentation for installation, usage, and troubleshooting!