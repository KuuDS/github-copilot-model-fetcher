#!/bin/bash
# Setup local scheduling for Copilot model fetching

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "Copilot Fetcher - Local Scheduler Setup"
echo "================================================"
echo ""

# Check if gh is authenticated
echo "Checking GitHub CLI authentication..."
if ! gh auth status >/dev/null 2>&1; then
    echo -e "${RED}✗ GitHub CLI not authenticated${NC}"
    echo ""
    echo "Please run: gh auth login"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ GitHub CLI authenticated${NC}"
echo ""

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

echo "Detected OS: $OS"
echo ""

# Setup based on OS
if [ "$OS" == "macos" ]; then
    echo "Setting up launchd service (macOS)..."
    
    PLIST_FILE="$HOME/Library/LaunchAgents/com.copilot-fetch.plist"
    
    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.copilot-fetch</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd $REPO_DIR && ./run.sh fetch</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/copilot-fetch.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/copilot-fetch.error</string>
</dict>
</plist>
EOF
    
    # Unload if exists
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    
    # Load service
    launchctl load "$PLIST_FILE"
    
    echo -e "${GREEN}✓ Service installed${NC}"
    echo ""
    echo "Service file: $PLIST_FILE"
    echo "Logs: /tmp/copilot-fetch.log"
    echo ""
    echo "Commands:"
    echo "  launchctl start com.copilot-fetch    # Run now"
    echo "  launchctl stop com.copilot-fetch     # Stop"
    echo "  launchctl unload $PLIST_FILE         # Uninstall"
    
elif [ "$OS" == "linux" ]; then
    echo "Setting up systemd timer (Linux)..."
    
    # Create directories
    mkdir -p ~/.config/systemd/user
    
    # Service file
    cat > ~/.config/systemd/user/copilot-fetch.service << EOF
[Unit]
Description=GitHub Copilot Model Fetcher
After=network.target

[Service]
Type=oneshot
WorkingDirectory=$REPO_DIR
ExecStart=$REPO_DIR/run.sh fetch
StandardOutput=append:/tmp/copilot-fetch.log
StandardError=append:/tmp/copilot-fetch.error
EOF
    
    # Timer file
    cat > ~/.config/systemd/user/copilot-fetch.timer << EOF
[Unit]
Description=Run Copilot Fetch daily at 2 AM

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
    
    # Reload and enable
    systemctl --user daemon-reload
    systemctl --user enable copilot-fetch.timer
    systemctl --user start copilot-fetch.timer
    
    echo -e "${GREEN}✓ Timer installed${NC}"
    echo ""
    echo "Service file: ~/.config/systemd/user/copilot-fetch.service"
    echo "Timer file: ~/.config/systemd/user/copilot-fetch.timer"
    echo "Logs: /tmp/copilot-fetch.log"
    echo ""
    echo "Commands:"
    echo "  systemctl --user start copilot-fetch      # Run now"
    echo "  systemctl --user stop copilot-fetch.timer # Stop timer"
    echo "  systemctl --user disable copilot-fetch.timer # Disable"
    echo ""
    echo "Status:"
    systemctl --user status copilot-fetch.timer --no-pager || true
fi

echo ""
echo -e "${GREEN}✓ Setup complete!${NC}"
echo ""
echo "The fetcher will run daily at 2:00 AM"
echo ""
echo "Test now with: ./run.sh fetch"
