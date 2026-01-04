#!/bin/bash

PISUGAR_SERVER="127.0.0.1"
PORT=8423

send_cmd() {
    echo "$1" | nc -w 1 $PISUGAR_SERVER $PORT
}

echo "🧪 PiSugar RTC Write Test"
echo "--------------------------------"

# 1. Check current state
echo "[1] Initial RTC:"
send_cmd "get rtc_time"

# 2. Prepare ISO Strings (Python style)
# We use Python to generate the EXACT string we are using in the app to reproduce the bug
ISO_NOW=$(python3 -c 'import datetime; t = datetime.datetime.now().astimezone(); s = t.strftime("%Y-%m-%dT%H:%M:%S%z"); print(s[:-2] + ":" + s[-2:] if s[-3] != ":" else s)')
echo "[2] Generated ISO String: $ISO_NOW"

# 3. Attempt Write
echo "   -> Sending: rtc_time $ISO_NOW"
RESP=$(send_cmd "rtc_time $ISO_NOW")
echo "   -> Response: $RESP"

sleep 2

# 4. Verify
echo "[3] Verified RTC (After Write):"
send_cmd "get rtc_time"

echo "--------------------------------"

# 5. Test Alarm Write
# Target: 1 hour later
ISO_ALARM=$(python3 -c 'import datetime; t = datetime.datetime.now().astimezone() + datetime.timedelta(hours=1); s = t.strftime("%Y-%m-%dT%H:%M:%S%z"); print(s[:-2] + ":" + s[-2:] if s[-3] != ":" else s)')
echo "[4] Generated Alarm String: $ISO_ALARM"

echo "   -> Sending: rtc_alarm_set $ISO_ALARM 127"
RESP=$(send_cmd "rtc_alarm_set $ISO_ALARM 127")
echo "   -> Response: $RESP"

sleep 1

echo "[5] Verified Alarm (After Write):"
send_cmd "get rtc_alarm_time"

echo "--------------------------------"
echo "Done."
