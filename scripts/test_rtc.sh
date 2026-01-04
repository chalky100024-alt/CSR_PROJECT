#!/bin/bash

PISUGAR_SERVER="127.0.0.1"
PORT=8423

send_cmd() {
    echo "$1" | nc -w 1 $PISUGAR_SERVER $PORT
}

# Python helper to generate format
gen_time() {
    # $1: Format string (e.g. "%Y-%m-%dT%H:%M:%S")
    # $2: UTC? (true/false)
    CMD="import datetime; t = datetime.datetime.now()"
    if [ "$2" == "true" ]; then
        CMD="$CMD.astimezone(datetime.timezone.utc)"
    else
        CMD="$CMD.astimezone()"
    fi
    CMD="$CMD.strftime('$1')"
    
    # Handle %z colon hack if needed
    python3 -c "$CMD"
}

echo "🧪 PiSugar RTC Format Brute-Force"
echo "--------------------------------"

# Format 1: ISO with Timezone (What we used)
F1=$(python3 -c 'import datetime; s = datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"); print(s[:-2] + ":" + s[-2:] if s[-3] != ":" else s)')
echo "[Try 1] ISO w/ Colon TZ: $F1"
echo "   -> $(send_cmd "rtc_time $F1")"

sleep 1

# Format 2: ISO No Timezone
F2=$(python3 -c 'import datetime; print(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))')
echo "[Try 2] ISO No TZ:       $F2"
echo "   -> $(send_cmd "rtc_time $F2")"

sleep 1

# Format 3: ISO UTC (Z suffix)
F3=$(python3 -c 'import datetime; print(datetime.datetime.now().astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))')
echo "[Try 3] ISO UTC (Z):     $F3"
echo "   -> $(send_cmd "rtc_time $F3")"

sleep 1

# Format 4: Space Separated
F4=$(python3 -c 'import datetime; print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))')
echo "[Try 4] Space Separator: $F4"
echo "   -> $(send_cmd "rtc_time $F4")"

echo "--------------------------------"
echo "Current RTC Status:"
send_cmd "get rtc_time"
