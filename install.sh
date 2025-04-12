#!/bin/bash

# Make sure the script is run with root privileges
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run with root privileges." 
    exit 1
fi

# Current directory and username
CURRENT_DIR=$(pwd)
USER=$(whoami)

# Ensure that requirements.txt exists
if [ ! -f "$CURRENT_DIR/requirements.txt" ]; then
    echo "requirements.txt not found. Please make sure the file exists."
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m pip install -r "$CURRENT_DIR/requirements.txt"

# Create the systemd service file
SERVICE_FILE="/etc/systemd/system/wolverine.service"

echo "Creating systemd service file..."

cat <<EOF > $SERVICE_FILE
[Unit]
Description=WOLverine Web Application
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$CURRENT_DIR
ExecStart=/usr/bin/python3 $CURRENT_DIR/app.py
Restart=always
Environment="FLASK_ENV=production"
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

# Set permissions for the service file
chmod 644 $SERVICE_FILE

# Enable and start the service
echo "Enabling and starting the WOLverine service..."
systemctl daemon-reload
systemctl enable wolverine.service
systemctl start wolverine.service

echo "Installation completed."
