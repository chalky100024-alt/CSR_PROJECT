
import socket

def send_cmd(cmd):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect(('127.0.0.1', 8423))
            s.sendall(cmd.encode())
            return s.recv(1024).decode('utf-8').strip()
    except Exception as e:
        return f"Error: {e}"

print("=== ⚡ Forcing Battery Boot Params ===")
print("-" * 30)

# 1. Force Battery Output ON (Crucial for battery-only boot)
print("1. Set Battery Output: ON (1)")
print(f"   Response: {send_cmd('set_battery_output 1')}")
print(f"   Check:    {send_cmd('get battery_output')}")

# 2. Force Button Enable ON (Just to be sure)
print("\n2. Set Button Enable: ON (1)")
print(f"   Response: {send_cmd('set_button_enable 1')}")
print(f"   Check:    {send_cmd('get button_enable')}")

print("-" * 30)
print("Done. Please unplug USB and press Reset.")
