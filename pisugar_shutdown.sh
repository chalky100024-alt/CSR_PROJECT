#!/bin/bash

# Configuration
API_URL="http://localhost:8080/api/system?action=shutdown"
LOG_FILE="/home/pi/CSR_PROJECT/pisugar_button.log"

echo "[$(date)] Shutdown Requested via PiSugar" >> $LOG_FILE

# Call API to shutdown
curl -s -X POST "$API_URL"
