
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

print("=== 🛠️ Fixing Boot Button Setting ===")
print("Restoring Button functionality (set_button_enable 1)...")

# Only enabling the button as requested. NOT touching anti-mistouch.
resp = send_cmd("set_button_enable 1")
print(f"Response: {resp}")

status = send_cmd("get button_enable")
print(f"Current Button Enable Status: {status}")

print("Done. Try booting with the button now.")
