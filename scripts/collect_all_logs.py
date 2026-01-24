
import subprocess
import os
import datetime

OUTPUT_FILE = "/home/pi/CSR_PROJECT/debug_report.txt"

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode('utf-8')
    except Exception as e:
        return f"[CMD FAILED] {cmd}: {e}"

with open(OUTPUT_FILE, "w") as f:
    f.write(f"=== 🕵️ CSR Project Debug Report ===\n")
    f.write(f"Generated: {datetime.datetime.now()}\n\n")

    f.write("--- 1. Disk Usage ---\n")
    f.write(run_cmd("df -h"))
    f.write("\n\n")

    f.write("--- 2. Python Service Status ---\n")
    f.write(run_cmd("systemctl status photoframe.service"))
    f.write("\n\n")

    f.write("--- 3. PiSugar Server Status ---\n")
    f.write(run_cmd("systemctl status pisugar-server"))
    f.write("\n\n")

    f.write("--- 4. Lifecycle Log (Last 100 lines) ---\n")
    f.write(run_cmd("tail -n 100 /home/pi/CSR_PROJECT/lifecycle_log.txt"))
    f.write("\n\n")

    f.write("--- 5. System Log (RTC/PiSugar keywords) ---\n")
    # Search for RTC, PiSugar, and Shutdown events since yesterday
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    f.write(run_cmd(f"journalctl --since '{yesterday}' | grep -iE 'rtc|pisugar|shutdown|photoframe' | tail -n 200"))
    f.write("\n\n")

    f.write("--- 6. Battery Power Check ---\n")
    f.write("Button Script Log:\n")
    f.write(run_cmd("tail -n 20 /home/pi/CSR_PROJECT/pisugar_button.log"))
    f.write("\n\n")

print(f"✅ Report saved to {OUTPUT_FILE}")
print("Run: cat " + OUTPUT_FILE)
