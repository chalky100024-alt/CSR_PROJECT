#!/bin/bash

# Configuration
SSID="MyFrame_Setup"
PASSWORD="12345678"  # Simple password for setup
IFNAME="wlan0"

echo "📡 Setting up Wi-Fi Hotspot (AP Mode) using NetworkManager..."

# 1. Delete existing connection if it exists
if nmcli connection show "$SSID" >/dev/null 2>&1; then
    echo "Existing connection '$SSID' found. Deleting..."
    sudo nmcli connection delete "$SSID"
fi

# 2. Create the Hotspot connection
# 802-11-wireless.mode ap: Access Point mode
# ipv4.method shared: Acts as a router (DHCP server)
echo "Creating new Hotspot connection..."
sudo nmcli con add type wifi ifname "$IFNAME" con-name "$SSID" autoconnect yes ssid "$SSID"
sudo nmcli con modify "$SSID" 802-11-wireless.mode ap
sudo nmcli con modify "$SSID" 802-11-wireless.band bg
sudo nmcli con modify "$SSID" ipv4.method shared

# 3. Set Security (WPA2)
# If you want OPEN network, comment these lines out
echo "Setting password..."
sudo nmcli con modify "$SSID" wifi-sec.key-mgmt wpa-psk
sudo nmcli con modify "$SSID" wifi-sec.psk "$PASSWORD"

# 4. Set Priority (optional, usually manual connection logic handles this)
# We want this to be a fallback, so priority low? 
# Actually, standard behavior: if known networks fail, user manually starts this or it falls back.
# For now, we just create it. To activate, we can use: sudo nmcli con up MyFrame_Setup

echo "✅ Hotspot '$SSID' created successfully!"
echo "----------------------------------------"
echo "To activate manually: sudo nmcli con up $SSID"
echo "Connect with Password: $PASSWORD"
echo "Access the Frame at: http://10.42.0.1:8080 (usually)"
