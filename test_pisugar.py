import socket
import datetime

def send_cmd(cmd):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect(('127.0.0.1', 8423))
            s.sendall(cmd.encode())
            resp = s.recv(1024).decode('utf-8').strip()
            print(f"CMD: '{cmd}' -> RESP: '{resp}'")
            return resp
    except Exception as e:
        print(f"CMD: '{cmd}' -> ERROR: {e}")
        return None

print("--- Testing PiSugar RTC Commands ---")

# 1. Get current RTC time (Baseline)
send_cmd("get rtc_time")

# 2. Try setting alarm with different formats (10 mins from now)
now = datetime.datetime.now()
future = now + datetime.timedelta(minutes=10)
iso_time = future.strftime("%Y-%m-%dT%H:%M:%S")

print(f"\nTrying to set alarm to: {iso_time}")

# Try 1: Standard (What failed?)
send_cmd(f"rtc_alarm_set {iso_time}")

# Try 2: With quotes
send_cmd(f"rtc_alarm_set \"{iso_time}\"")

# Try 3: rtc_alarm_set_time (Alternative name)
send_cmd(f"rtc_alarm_set_time {iso_time}")

# Try 4: set_rtc_alarm_time (Another alternative)
send_cmd(f"set_rtc_alarm_time {iso_time}")

print("\n--- Test Complete ---")
