
import socket

def send_cmd(cmd):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect(('127.0.0.1', 8423))
            s.sendall(cmd.encode())
            return s.recv(4096).decode('utf-8').strip() # Larger buffer for help text
    except Exception as e:
        return f"Error: {e}"

print("=== PiSugar Command List ===")
print(send_cmd("help"))
print("============================")
