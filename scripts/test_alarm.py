
import socket
import datetime
import time

def send_cmd(cmd):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect(('127.0.0.1', 8423))
            s.sendall(cmd.encode())
            return s.recv(1024).decode('utf-8').strip()
    except Exception as e:
        return f"Error: {e}"

print("=== 🧪 PiSugar Alarm Test ===")
print("-" * 30)
# PROBE: Check available commands to find valid timer options
print("🔍 Probing Server Commands ('help')...")
print(send_cmd("help"))
print(send_cmd("List"))
print(send_cmd("?"))
print("-" * 30)
rtc_raw = send_cmd("get rtc_time")
print(f"Device RTC Time Raw: '{rtc_raw}'")

if "iso" in rtc_raw or "rtc_time" in rtc_raw:
    # Cleanup prefix "rtc_time: " if present
    if ":" in rtc_raw: 
        rtc_val = rtc_raw.split(":", 1)[1].strip() 
    else: 
        rtc_val = rtc_raw.strip()
else:
    # Fallback if get failed
    rtc_val = datetime.datetime.now().astimezone().isoformat()

print(f"Device RTC Time Val: '{rtc_val}'")

# 2. Parse it to add 2 minutes
# The device format is likely: 2026-01-12T23:33:38.000+09:00
# We need to preserve this structure EXACTLY.
try:
    # Try parsing full ISO
    cur_dt = datetime.datetime.fromisoformat(rtc_val)
except:
    # Fallback to local
    cur_dt = datetime.datetime.now().astimezone()

target_dt = cur_dt + datetime.timedelta(minutes=2)

# 3. Format back EXACTLY like input (ISO with T, .000 ms, and Timezone)
# Python isoformat() usually does this well
target_str = target_dt.isoformat(timespec='milliseconds')
print(f"Target Time (Mimic): {target_str}")

# standard command with REPEAT=127 (Daily)
cmd = f"rtc_alarm_set {target_str} 127"
print(f"Sending CMD: '{cmd}'")

resp = send_cmd(cmd)
print(f"Response:    '{resp}'")

if "ok" in resp.lower() or "done" in resp.lower() or "success" in resp.lower():
    print("✅ Alarm Set Command ACCEPTED")
    # rtc_alarm_enable is INVALID. rtc_alarm_set AUTO-ENABLES.
    # We should check "get rtc_alarm_enabled" to verify.
else:
    print("❌ Alarm Set Command FAILED (Check syntax or connection)")
    exit(1)

print("-" * 30)
print("Checking Status...")

# Check ENABLED status (True = Active, False = Disabled)
enabled_status = send_cmd("get rtc_alarm_enabled")
print(f"Alarm Enabled: {enabled_status}")

# Check FLAG (True = Fired/IRQ, False = Waiting)
flag = send_cmd("get rtc_alarm_flag")
print(f"Alarm Flag:  {flag} (False means Waiting/Pending)")

# Retry reading time to avoid I/O error
time_chk = "Error"
for i in range(3):
    time_chk = send_cmd("get rtc_alarm_time")
    if "Error" not in time_chk and "I/O" not in time_chk:
        break
    time.sleep(0.5)

print(f"Alarm Time:  {time_chk}")

if "true" in enabled_status.lower():
    print("🎉 SUCCESS: Alarm is ACTIVE (Enabled=True).")
else:
    print("⚠️ WARNING: Alarm is set but ENABLED is FALSE.")

print("=============================")
