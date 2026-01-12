
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
# Format: ISO 8601 with timezone (e.g., 2026-01-12T22:40:00+09:00)
target_iso = target.strftime("%Y-%m-%dT%H:%M:%S%z")
# Insert colon in timezone if needed (+0900 -> +09:00)
if len(target_iso) > 5 and target_iso[-3] != ':':
    target_iso = target_iso[:-2] + ':' + target_iso[-2:]

print(f"Target Time:  {target_iso}")

# standard command WITHOUT repeat argument (Try to force One-Shot Date)
cmd = f"rtc_alarm_set {target_iso}"
print(f"Sending CMD: '{cmd}'")

resp = send_cmd(cmd)
print(f"Response:    '{resp}'")

print("-" * 30)
print("Checking Flag...")
flag = send_cmd("get rtc_alarm_flag")
print(f"Alarm Flag:  {flag}")

time_chk = send_cmd("get rtc_alarm_time")
print(f"Alarm Time:  {time_chk}")

if "ok" in resp.lower() or "done" in resp.lower() or "success" in resp.lower():
    print("✅ Alarm Set Command ACCEPTED")
    # Enable
    send_cmd("rtc_alarm_enable")
    print("✅ Alarm Enabled")
else:
    print("❌ Alarm Set Command FAILED (Check syntax or connection)")

print("=============================")
