
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

print("=== 🔋 PiSugar Power Diagnostic ===")
print("-" * 40)

# 1. Hardware Info
print(f"Firmware: {send_cmd('get version')}")
print(f"Model:    {send_cmd('get model')}")

# 2. Battery Health
print("\n[Battery Status]")
print(f"Level:    {send_cmd('get battery')}")
print(f"Voltage:  {send_cmd('get battery_voltage')} mV")
print(f"Charging: {send_cmd('get battery_power_plugged')}")

# 3. Boot & Button Settings
print("\n[Boot Config]")
print(f"Button Enable:     {send_cmd('get button_enable')}")
print(f"Anti-Mistouch:     {send_cmd('get anti_mistouch')}")
print(f"Auto Power On:     {send_cmd('get auto_power_on')}")

# 4. Protection & Output
print("\n[Protection & Output]")
print(f"Battery Output:    {send_cmd('get battery_output')}")
print(f"Safe Shutdown Lvl: {send_cmd('get safe_shutdown_level')}")
print(f"Input Protect:     {send_cmd('get input_protect')}")

print("\n===============================")
