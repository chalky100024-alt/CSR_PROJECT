
import socket
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

print("=== 🛠️ Resetting PiSugar Power Config ===")
print("Objective: Ensure Button Boot works on Battery.")
print("-" * 40)

commands = [
    ("Battery Output", "set_battery_output 1"),        # Force Output ON
    ("Button Enable",  "set_button_enable 1"),         # Force Button ON
    ("Anti Mistouch",  "set_anti_mistouch 0"),         # Disable Mistouch (Safety)
    ("Input Protect",  "set_input_protect 1"),         # Standard
    ("Safe Shutdown",  "set_safe_shutdown_level 5"),   # Lower limit to 5%
    ("Auto Power On",  "set_auto_power_on 0")          # Disable auto-on plug (Optional)
]

for name, cmd in commands:
    print(f"Executing {name} ({cmd})...")
    resp = send_cmd(cmd)
    print(f"   -> Response: {resp}")
    time.sleep(0.5)

print("-" * 40)
print("✅ Configuration Reset Complete.")
print("👉 Please unplug USB and test the Reset Button now.")
