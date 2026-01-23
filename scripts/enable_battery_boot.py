
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

print("=== 🔋 Configuring PiSugar for Battery Boot ===")
print("-" * 40)

# 1. Disable Anti-Mistouch (This blocks battery boot!)
print("1. Disabling Anti-Mistouch (set_anti_mistouch 0)...")
resp1 = send_cmd("set_anti_mistouch 0")
print(f"   Response: {resp1}")

# 2. Enable Physical Button (Just in case)
print("2. Enabling Physical Button (set_button_enable 1)...")
resp2 = send_cmd("set_button_enable 1")
print(f"   Response: {resp2}")

# 3. Verification
print("-" * 40)
print("Verification:")
print(f"   Anti-Mistouch Status: {send_cmd('get anti_mistouch')}") # 'get' might need specific variable name, probing
print(f"   Button Enable Status: {send_cmd('get button_enable')}")

print("\n✅ Configuration Done.")
print("👉 Now you can unplug USB and try pressing the Reset Button to boot!")
