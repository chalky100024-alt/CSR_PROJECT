# 📡 Wi-Fi Setup Guide (Hotspot Mode)

This guide explains how to configure your Photo Frame to broadcast its own Wi-Fi network (`MyFrame_Setup`) for initial setup.

## 1. Setup on Raspberry Pi
Run the provided script to create the Hotspot connection:

```bash
cd ~/CSR_PROJECT
chmod +x scripts/setup_hotspot.sh
./scripts/setup_hotspot.sh
```

To activate the hotspot manually (e.g., if home Wi-Fi is not found):
```bash
sudo nmcli con up MyFrame_Setup
```

## 2. Using the QR Code
You can create a QR code that automatically connects a smartphone to this hotspot.

**QR Code Content:**
```
WIFI:S:MyFrame_Setup;T:WPA;P:12345678;;
```
*(Copy and paste this string into any QR Code Generator website)*

## 3. User Workflow
1.  **Scan QR Code:** User scans the code on the back of the frame.
2.  **Connect:** Phone connects to `MyFrame_Setup` Wi-Fi.
3.  **Open Settings:** User opens a browser and goes to:
    - `http://10.42.0.1:8080` (Default setup IP)
    - OR `http://myframe.local:8080` (If mDNS works)
4.  **Configure:**
    - Go to **Settings** -> **System**.
    - Click **[Scan Networks]**.
    - Select Home Wi-Fi and enter password.
    - Click **Connect**.
5.  **Finish:** Frame reboots and connects to the Home Wi-Fi.

## 4. Resetting to Setup Mode
If the user changes routers or moves, they need to get back to this mode.
- **Physical Button (Recommended):** Map a long-press of the PiSugar button to run `sudo nmcli con up MyFrame_Setup`.
- **Automatic Fallback:** Configure Raspberry Pi to auto-connect to `MyFrame_Setup` if other networks fail (requires advanced script).
