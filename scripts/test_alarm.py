
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
now = datetime.datetime.now().astimezone()
print(f"Current Time: {now}")

# Target: +2 minutes
target = now + datetime.timedelta(minutes=2)

# Format: UTC ISO 8601 (Z suffix)
# Force UTC to avoid timezone parsing issues on hardware
target_utc = target.astimezone(datetime.timezone.utc)
target_iso = target_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

print(f"Target Time (UTC): {target_iso}")

# standard command with REPEAT=127 (Daily)
# This prevents the "Past Date" disable issue
cmd = f"rtc_alarm_set {target_iso} 127"
print(f"Sending CMD: '{cmd}'")

resp = send_cmd(cmd)
print(f"Response:    '{resp}'")

if "ok" in resp.lower() or "done" in resp.lower() or "success" in resp.lower():
    print("✅ Alarm Set Command ACCEPTED")
    # Enable FIRST before checking flag
    send_cmd("rtc_alarm_enable")
    print("✅ Alarm Enabled Signal Sent")
else:
    print("❌ Alarm Set Command FAILED (Check syntax or connection)")
    exit(1)

print("-" * 30)
print("Checking Flag...")
flag = send_cmd("get rtc_alarm_flag")
print(f"Alarm Flag:  {flag}")

# Retry reading time to avoid I/O error
time_chk = "Error"
for i in range(3):
    time_chk = send_cmd("get rtc_alarm_time")
    if "Error" not in time_chk and "I/O" not in time_chk:
        break
    time.sleep(0.5)

print(f"Alarm Time:  {time_chk}")

if "true" in flag.lower():
    print("🎉 SUCCESS: Alarm is SET and ENABLED.")
else:
    print("⚠️ WARNING: Alarm is set but Flag is FALSE. (Maybe enable failed?)")

print("=============================")
