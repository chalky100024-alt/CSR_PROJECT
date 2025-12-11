#!/bin/bash

# setup_drivers.sh
# Waveshare 7.3inch e-Paper HAT (F) Driver Installer

echo ">>> Waveshare Driver Setup Start..."

WORKDIR=$(pwd)
TEMP_DIR="temp_waveshare_repo"
TARGET_LIB="$WORKDIR/lib"

# 1. Create lib directory if not exists
if [ ! -d "$TARGET_LIB" ]; then
    echo "Creating lib directory..."
    mkdir -p "$TARGET_LIB"
    touch "$TARGET_LIB/__init__.py"
fi

# 2. Clone Waveshare e-Paper repo (Sparse checkout or full clone)
echo "Cloning Waveshare e-Paper repository (this may take a moment)..."
git clone --depth 1 https://github.com/waveshare/e-Paper.git "$TEMP_DIR"

if [ ! -d "$TEMP_DIR" ]; then
    echo "ERROR: Git clone failed. Check internet connection."
    exit 1
fi

# 3. Copy necessary files for 7.3inch (F)
# Source path usually: RaspberryPi_JetsonNano/python/lib/waveshare_epd
SRC_DRIVER="$TEMP_DIR/RaspberryPi_JetsonNano/python/lib/waveshare_epd"

if [ -d "$SRC_DRIVER" ]; then
    echo "Copying driver files..."
    cp -r "$SRC_DRIVER" "$TARGET_LIB/"
    echo "Driver copied to $TARGET_LIB/waveshare_epd"
else
    echo "ERROR: Driver source path not found in repo."
    rm -rf "$TEMP_DIR"
    exit 1
fi

# 4. Cleanup
echo "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

echo ">>> Setup Complete! 'waveshare_epd' is now in ./lib"
echo "You can now run 'python3 app.py'"
