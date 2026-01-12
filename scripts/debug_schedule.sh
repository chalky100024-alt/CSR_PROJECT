#!/bin/bash
echo "=== 🕵️‍♂️ PhotoFrame Scheduler Debugger ==="
echo "Date: $(date)"
echo "----------------------------------------"

# 1. Check Custom Lifecycle Log
echo "📄 [lifecycle_log.txt] (Full Content)"
if [ -f ../lifecycle_log.txt ]; then
    cat ../lifecycle_log.txt
else
    echo "❌ lifecyle_log.txt not found!"
fi
echo "----------------------------------------"

# 1.5 Check System Boot History
echo "🖥️ [System Boot History]"
last reboot | head -n 5
echo "----------------------------------------"

# 2. Check PiSugar RTC & Alarm
echo "⏰ [PiSugar Status]"
echo "System Time: $(date)"
if command -v nc >/dev/null; then
    echo "RTC Time:    $(echo "get rtc_time" | nc -w 1 127.0.0.1 8423)"
    echo "Battery:     $(echo "get battery" | nc -w 1 127.0.0.1 8423)"
    echo "Alarm Info:  $(echo "get rtc_alarm_get" | nc -w 1 127.0.0.1 8423)"
    echo "Alarm Flag:  $(echo "get rtc_alarm_flag" | nc -w 1 127.0.0.1 8423)"
else
    echo "❌ 'nc' (netcat) not found. Cannot queries PiSugar directly."
fi
echo "----------------------------------------"

# 3. Check Service Failure Logs
echo "⚙️ [Service Logs] (Last boot failures/errors)"
sudo journalctl -u photoframe.service -n 20 --no-pager
echo "----------------------------------------"

echo "✅ Debug info collection complete."
