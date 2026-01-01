#!/bin/bash

# Configuration
API_URL="http://localhost:8080/api/system?action=toggle_mode"
LOG_FILE="/home/pi/CSR_PROJECT/pisugar_button.log"

# Log time
echo "[$(date)] Button Pressed" >> $LOG_FILE

# Call API to toggle mode
RESPONSE=$(curl -s -X POST "$API_URL")
echo "Response: $RESPONSE" >> $LOG_FILE

# Optional: Feedback via PiSugar LED or E-Ink (if complex)
# For now, just logging.
