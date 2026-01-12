
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

# Format: ISO 8601 with timezone (No Colon in TZ)
# Standard Python %z gives +0900. Previous code manually added ':'.
# Maybe PiSugar wants +0900?
target_iso = target.strftime("%Y-%m-%dT%H:%M:%S%z")

print(f"Target Time:  {target_iso} (No Colon in TZ)")

# standard command with REPEAT=0 (One-Shot)
cmd = f"rtc_alarm_set {target_iso} 0"
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
