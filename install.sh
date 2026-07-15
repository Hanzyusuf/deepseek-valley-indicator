#!/bin/bash
# Installation script - No external Python packages needed!

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Installing Valley Systray Indicator...${NC}"

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python $REQUIRED_VERSION or higher required (found $PYTHON_VERSION)${NC}"
    echo "Please install Python 3.9+ which includes zoneinfo"
    exit 1
fi

echo -e "${GREEN}Python $PYTHON_VERSION detected (zoneinfo available)${NC}"

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
sudo apt update
sudo apt install -y python3 python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Create installation directory
INSTALL_DIR="$HOME/.local/share/valley-indicator"
mkdir -p "$INSTALL_DIR"

# Create desktop applications directory if it doesn't exist
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$HOME/.config/autostart"

# Copy files
echo -e "${YELLOW}Installing files...${NC}"
if [ -f "valley_indicator.py" ] && [ -f "scheduler.py" ] && [ -f "schedules.json" ]; then
    cp valley_indicator.py scheduler.py schedules.json run_indicator.sh "$INSTALL_DIR/"
else
    echo -e "${RED}Error: Required files not found in current directory${NC}"
    echo "Make sure you have: valley_indicator.py, scheduler.py, schedules.json, run_indicator.sh"
    exit 1
fi

chmod +x "$INSTALL_DIR/valley_indicator.py"
chmod +x "$INSTALL_DIR/run_indicator.sh"

# Create desktop entry
echo -e "${YELLOW}Creating desktop entry...${NC}"
cat > "$HOME/.local/share/applications/valley-indicator.desktop" << EOF
[Desktop Entry]
Name=Deepseek Valley Status Indicator
Comment=Time-based status indicator for XFCE panel
Exec=$INSTALL_DIR/run_indicator.sh
Icon=applications-system
Terminal=false
Type=Application
StartupNotify=true
X-GNOME-Autostart-enabled=true
EOF

# Setup autostart
echo -e "${YELLOW}Setting up autostart...${NC}"
cp "$HOME/.local/share/applications/valley-indicator.desktop" \
   "$HOME/.config/autostart/"

echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo -e "To start the indicator now:"
echo -e "  ${YELLOW}$INSTALL_DIR/run_indicator.sh${NC}"
echo ""
echo -e "To test scheduler:"
echo -e "  ${YELLOW}cd $INSTALL_DIR && python3 scheduler.py${NC}"
echo ""
echo -e "To add to panel if icon doesn't appear:"
echo -e "  ${YELLOW}Right-click panel -> Panel Preferences -> Items -> Add 'Status Tray'${NC}"
echo ""
echo -e "Logs: ${YELLOW}$HOME/.cache/valley-indicator/indicator.log${NC}"
echo ""
echo -e "To uninstall:"
echo -e "  ${YELLOW}rm -rf $INSTALL_DIR ~/.config/autostart/valley-indicator.desktop ~/.local/share/applications/valley-indicator.desktop${NC}"