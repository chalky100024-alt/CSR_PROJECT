#!/bin/bash

# Configuration
PISUGAR_SERVER="127.0.0.1"
PORT=8423

echo "========================================"
echo "🔋 PiSugar Diagnostics Routine"
echo "========================================"

# Function to send command to PiSugar
send_cmd() {
    echo "$1" | nc -w 1 $PISUGAR_SERVER $PORT
}

# 1. System Info
echo "[1] System Time:"
date
echo ""

# 2. Battery Status
echo "[2] Battery Status:"
BAT=$(send_cmd "get battery")
PLUG=$(send_cmd "get battery_power_plugged")
echo "   Level: $BAT"
echo "   Plugged: $PLUG"
echo ""

# 3. RTC Info
echo "[3] RTC Status:"
RTC_TIME=$(send_cmd "get rtc_time")
ALARM_ENABLED=$(send_cmd "get rtc_alarm_enabled")
ALARM_TIME=$(send_cmd "get rtc_alarm_time")

echo "   Current RTC Time: $RTC_TIME"
echo "   Alarm Enabled:    $ALARM_ENABLED"
echo "   Target Alarm:     $ALARM_TIME"
echo ""

# 4. Analysis
echo "[4] Analysis:"
if [[ "$PLUG" == *"true"* ]]; then
    echo "   ✅ Power cable connected."
else
    echo "   ⚠️ Running on Battery."
fi

# Compare Time (Simple Visual Check)
echo "   -> Compare 'System Time' vs 'RTC Time' above."
echo "   -> They should be nearly identical."
echo "========================================"
