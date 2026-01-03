#!/bin/bash

BACKUP_DIR="$HOME/wifi_backup_$(date +%Y%m%d_%H%M%S)"
NM_DIR="/etc/NetworkManager/system-connections"

echo "💾 Backing up Wi-Fi profiles to $BACKUP_DIR..."

mkdir -p "$BACKUP_DIR"

# Copy all connection files (requires sudo because they are protected)
sudo cp "$NM_DIR"/*.nmconnection "$BACKUP_DIR/" 2>/dev/null

# Also backup config.json just in case
if [ -f "config.json" ]; then
    cp config.json "$BACKUP_DIR/"
fi

echo "✅ Backup Complete!"
echo "Files saved in: $BACKUP_DIR"
echo "To restore later, run:"
echo "sudo cp $BACKUP_DIR/*.nmconnection $NM_DIR/ && sudo nmcli con reload"
