#!/bin/bash
# FL-IDS Client Agent Installer
# Usage: curl -sSL https://your-domain.com/install.sh | FLDS_API_KEY=your-key FLDS_SERVER_URL=https://your-server.com bash

echo "Installing FL-IDS Client Agent..."

# Check Python version
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is required but not found. Please install Python 3.9+."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Detected Python $PYTHON_VERSION"

# Install requirements
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Create .env file
echo "Creating .env file..."
cat << EOF > .env
FLDS_SERVER_URL=${FLDS_SERVER_URL:-http://localhost:8000}
FLDS_API_KEY=${FLDS_API_KEY:-}
FLDS_INTERFACE=${FLDS_INTERFACE:-}
FLDS_CAPTURE_DURATION=${FLDS_CAPTURE_DURATION:-300}
FLDS_LOCAL_EPOCHS=${FLDS_LOCAL_EPOCHS:-3}
FLDS_POLL_INTERVAL=${FLDS_POLL_INTERVAL:-60}
EOF

# OS specific setup
OS=$(uname -s)
if [ "$OS" = "Linux" ]; then
    echo "Creating systemd service..."
    cat << EOF > /tmp/flds-agent.service
[Unit]
Description=FL-IDS Agent
After=network.target

[Service]
ExecStart=$(which python3) $(pwd)/agent.py
WorkingDirectory=$(pwd)
Restart=always
User=$(whoami)

[Install]
WantedBy=multi-user.target
EOF
    echo "To install as a service, run: sudo mv /tmp/flds-agent.service /etc/systemd/system/ && sudo systemctl enable --now flds-agent"
elif [ "$OS" = "Darwin" ]; then
    echo "Creating launchd plist..."
    PLIST_PATH="$HOME/Library/LaunchAgents/com.flds.agent.plist"
    cat << EOF > $PLIST_PATH
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.flds.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(which python3)</string>
        <string>$(pwd)/agent.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$(pwd)</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF
    echo "Created $PLIST_PATH. To load the service run: launchctl load $PLIST_PATH"
fi

echo "========================================="
echo "Installation complete!"
echo "You can start the agent manually by running:"
echo "python3 agent.py"
echo "========================================="
