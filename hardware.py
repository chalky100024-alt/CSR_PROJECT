import os
import sys
import socket
import logging
import subprocess
import time

logger = logging.getLogger(__name__)

# Mock Mode 확인
IS_RPI = os.path.exists("/sys/firmware/devicetree/base/model")

class HardwareController:
    def __init__(self):
        self.epd = None
        self.init_error = None
        if IS_RPI:
            try:
                # Try importing from pip package (standard way)
                from waveshare_epd import epd7in3f
                self.epd = epd7in3f.EPD()
                logger.info("E-Ink Driver Loaded.")
                
            except ImportError:
                 # Critical fix: Don't crash, just disable hardware
                 self.init_error = "Missing 'waveshare_epd'. Run: git clone https://github.com/waveshare/e-Paper.git and copy lib/waveshare_epd to here."
                 logger.error(f"[Hardware Warning] {self.init_error}")
                 self.epd = None
            except Exception as e:
                self.init_error = str(e)
                logger.warning(f"E-Ink Driver Init Failed: {e}")

    def display_image(self, pil_image):
        """이미지를 E-Ink에 전송"""
        if not self.epd:
            if IS_RPI:
                logger.error(f"[Hardware Fail] E-Ink Driver load failed previously. Error: {self.init_error}")
            else:
                logger.info("[Mock] E-Ink 업데이트 흉내 (PC 모드)")
            return True
        
        try:
            logger.info("E-Ink Hardware Init...")
            self.epd.init()
            # 7-Color Palette Quantization
            # (팔레트 처리 로직은 생략하고, 라이브러리 기본 제공 함수 사용 권장)
            # 여기서는 편의상 바로 버퍼 전송 시도 (실제론 팔레트 매핑 필요)
            self.epd.display(self.epd.getbuffer(pil_image))
            self.epd.sleep()
            logger.info("E-Ink Update Done.")
            return True
        except Exception as e:
            logger.error(f"E-Ink Display Error: {e}")
            return False

    def pisugar_command(self, cmd):
        """PiSugar TCP 서버로 명령 전송"""
        if not IS_RPI: 
            # Mock Data for Development
            if cmd == 'get battery': return "battery: 85"
            if cmd == 'get battery_power_plugged': return "battery_power_plugged: true"
            return "ok"
            
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect(('127.0.0.1', 8423))
                s.sendall(cmd.encode())
                response = s.recv(1024).decode('utf-8').strip()
                logger.debug(f"PiSugar CMD: {cmd} -> {response}")
                return response
        except Exception as e:
            logger.error(f"PiSugar Error: {e}")
            return None

    def get_battery_status(self):
        """배터리 상태 조회 (퍼센트, 충전중 여부)"""
        try:
            # 1. Get Battery Level
            bat_res = self.pisugar_command('get battery')
            level = 0
            if bat_res:
                # Expected format: "battery: 85"
                params = bat_res.split(':')
                if len(params) > 1:
                    level = float(params[1].strip())

            # 2. Get Charging Status
            # 'battery_power_plugged' detects if USB is plugged in
            plug_res = self.pisugar_command('get battery_power_plugged')
            charging = False
            if plug_res:
                # Expected format: "battery_power_plugged: true"
                charging = 'true' in plug_res.lower()
            
            return {
                "level": level,
                "charging": charging
            }
        except Exception as e:
            logger.error(f"Battery Status Error: {e}")
            return {"level": 0, "charging": False}

    def scan_wifi(self):
        """nmcli를 이용한 와이파이 스캔"""
        if not IS_RPI:
            return [{"ssid": "Test_WiFi_1", "signal": 90}, {"ssid": "Test_WiFi_2", "signal": 60}]
        
        try:
            # sudo 권한 필요할 수 있음 (visudo 설정 권장)
            cmd = "nmcli -t -f SSID,SIGNAL dev wifi list"
            result = subprocess.check_output(cmd, shell=True).decode('utf-8')
            networks = []
            seen = set()
            for line in result.split('\n'):
                if not line: continue
                parts = line.split(':')
                ssid = parts[0]
                if ssid and ssid not in seen:
                    networks.append({"ssid": ssid, "signal": parts[1]})
                    seen.add(ssid)
            return networks
        except:
            return []

    def connect_wifi(self, ssid, password):
        """nmcli로 와이파이 연결"""
        if not IS_RPI:
            logger.info(f"[Mock] Connecting to {ssid}...")
            return True
        
        cmd = f"sudo nmcli dev wifi connect '{ssid}' password '{password}'"
        return os.system(cmd) == 0
