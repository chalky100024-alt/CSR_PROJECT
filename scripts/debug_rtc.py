
import socket
import datetime
import time
import sys

def send_cmd(cmd):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect(('127.0.0.1', 8423))
            s.sendall(cmd.encode())
            return s.recv(1024).decode('utf-8').strip()
    except Exception as e:
        return f"Error: {e}"

print("========================================")
print("🔎 PiSugar Deep Debugger v1.0")
print("========================================")

# 1. Firmware Version
print(f"1. Firmware Version:   {send_cmd('get version')}")
print(f"2. Model:              {send_cmd('get model')}")

# 2. Battery & Power
print("\n[Power State]")
print(f"   Battery:            {send_cmd('get battery')}")
print(f"   Battery Voltage:    {send_cmd('get battery_voltage')}")
print(f"   Power Plugged:      {send_cmd('get battery_power_plugged')}")

# 3. Current RTC State
print("\n[Current RTC State]")
rtc_time = send_cmd('get rtc_time')
print(f"   RTC Time:           {rtc_time}")
alarm_time = send_cmd('get rtc_alarm_time')
print(f"   Alarm Time:         {alarm_time}")
enabled = send_cmd('get rtc_alarm_enabled')
print(f"   Alarm Enabled:      {enabled}")
flag = send_cmd('get rtc_alarm_flag')
print(f"   Alarm Flag:         {flag}")

# 4. System Log Analysis (Historical)
print("\n[System Log Analysis - Last 5 RTC Events]")
try:
    # Try grabbing recent RTC related logs from syslog
    import subprocess
    cmd = "grep -ia 'rtc' /var/log/syslog | tail -n 5"
    logs = subprocess.getoutput(cmd)
    if not logs:
        logs = "[No matching logs found in syslog]"
    print(logs)
except Exception as e:
    print(f"   Could not read syslog: {e}")

# 5. Test Set Output
print("\n[Test: Set Alarm (+2 min, Repeat=127)]")
try:
    if "iso" in rtc_time or "rtc_time" in rtc_time:
         clean_str = rtc_time.split(":", 1)[1].strip() if ":" in rtc_time else rtc_time.strip()
         base_dt = datetime.datetime.fromisoformat(clean_str)
    else:
         base_dt = datetime.datetime.now().astimezone()

    target_dt = base_dt + datetime.timedelta(minutes=2)
    target_str = target_dt.isoformat(timespec='milliseconds')
    
    cmd = f"rtc_alarm_set {target_str} 127"
    print(f"   Command:            {cmd}")
    resp = send_cmd(cmd)
    print(f"   Response:           {resp}")
    
    time.sleep(1)
    
    # Check Result
    new_enabled = send_cmd('get rtc_alarm_enabled')
    print(f"   Enabled After Set:  {new_enabled}")
    
    if "false" in new_enabled.lower():
        print("   ❌ CRITICAL: Alarm disabled itself immediately!")
    else:
        print("   ✅ Verified: Alarm is Enabled.")

except Exception as e:
    print(f"   ❌ Exception: {e}")

print("\n========================================")
print("Please copy the output above and share it.")
