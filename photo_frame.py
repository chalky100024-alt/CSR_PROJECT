#!/usr/bin/env python3
import os
import sys
import time
import random
import json
import logging
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import requests
import threading

# Use project settings
import settings
import data_api
import renderer # Use renderer to create composed image
import hardware # Use existing hardware controller wrapper if compatible
# But user code imports waveshare directly in try/except.
# We will adopt user's direct approach for EPD to be safe with their provided code,
# OR use hardware.py if it wraps it well.
# User code has specific display logic (7 color palette etc).
# Best to keep user's logic self-contained but use settings for config.

from PIL import Image, ImageEnhance, ImageDraw, ImageFont

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- [경로 및 설정 정의] ---
# settings.py defines these, we should use them to be consistent
BASE_DIR = settings.BASE_DIR
UPLOADS_DIR = settings.UPLOADS_DIR
# PREVIEW_PATH = settings.PREVIEW_PATH # User code uses static/preview.jpg

# Waveshare 라이브러리 경로 설정 (User provided)
lib_dir = os.path.join(BASE_DIR, 'lib')
if os.path.exists(lib_dir):
    sys.path.append(lib_dir)

try:
    from waveshare_epd import epd7in3f
    HAS_EPD = True
except ImportError:
    HAS_EPD = False

def _safe_float(val):
    """Safely convert string to float, stripping units if present."""
    if not val: return 0.0
    try:
        # Strip common units (mm, C, %, etc) - simple numeric extraction
        import re
        # Find first potential float number in string
        match = re.search(r"[-+]?\d*\.\d+|\d+", str(val))
        if match:
            return float(match.group())
        return float(val)
    except:
        return 0.0

class EInkPhotoFrame:
    def __init__(self):
        self.epd = None
        # Check command line for preview
        self.is_preview_mode = ('--preview' in sys.argv)
        
        # Load Config via Settings (Secure)
        self.config = settings.load_config()
        
        self.display_width = 800
        self.display_height = 480

        # API Keys - Load from config (Empty by default, secure)
        # Try specific keys first, then generic fallback (as user code did)
        self.airkorea_api_key = self.config.get('api_key_air', self.config.get('api_key', ""))
        self.kma_weather_api_key = self.config.get('api_key_kma', self.config.get('api_key', ""))
        
        self.station_name = self.config.get('station_name', "고덕")
        loc = self.config.get('location', {})
        self.kma_nx = int(loc.get('nx', 61))
        self.kma_ny = int(loc.get('ny', 115))

        # 사진 경로
        self.photos_dir = getattr(settings, 'UPLOADS_DIR', UPLOADS_DIR)
        
        # 폰트 경로들
        self.font_paths = [
            os.path.join(BASE_DIR, "AppleSDGothicNeoB.ttf"), # 1. User Provided (Best)
            os.path.join(BASE_DIR, "Apple_산돌고딕_Neo", "AppleSDGothicNeoEB.ttf"),
            os.path.join(BASE_DIR, "Apple_산돌고딕_Neo", "AppleSDGothicNeoB.ttf"),
            "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        ]

        self.icon_dir = os.path.join(BASE_DIR, "icons")
        # self.weather_icons = self._load_weather_icons() # Removed: Renderer handles this, and method was missing causing crash.

        if self.is_preview_mode:
            logger.info(">> 미리보기 모드 실행 (E-Ink 갱신 없음)")
        elif HAS_EPD:
            try:
                self.epd = epd7in3f.EPD()
                logger.info("✅ Waveshare EPD 객체 생성 성공 (7.3인치 F타입)")
            except Exception as e:
                logger.error(f"❌ E-Ink 객체 생성 실패: {e}")
                self.epd = None
        else:
            logger.warning("⚠️ Waveshare 라이브러리를 찾을 수 없어 미리보기 모드로 전환합니다.")

    def get_7color_palette(self):
        standard_7_colors = [0, 0, 0, 255, 255, 255, 255, 0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 0, 255, 165, 0]
        filler = [255, 255, 255]
        full_palette_data = standard_7_colors + filler * (256 - len(standard_7_colors) // 3)
        palette_image = Image.new('P', (1, 1), 0)
        palette_image.putpalette(full_palette_data[:768])
        return palette_image



    def init_display(self):
        if self.is_preview_mode: return True
        if self.epd:
            try:
                self.epd.init()
                return True
            except:
                return False
        return False

    def get_fine_dust_data(self):
        # Delegate to shared data_api for consistency
        return data_api.get_fine_dust_data(self.airkorea_api_key, self.station_name)

    def get_weather_data(self):
        # Delegate to shared data_api for consistency
        return data_api.get_weather_data(self.kma_weather_api_key, self.kma_nx, self.kma_ny)

    def get_photo_list(self):
        if not os.path.exists(self.photos_dir): return []
        exts = ('.jpg', '.jpeg', '.png', '.bmp')
        return [os.path.join(self.photos_dir, f) for f in os.listdir(self.photos_dir) if
                f.lower().endswith(exts) and not f.startswith('.')]





    def get_kma_base_time(self, api_type='ultrasrt'):
        now = datetime.now()
        base_date = now.strftime('%Y%m%d')
        if now.minute < 40:
            if now.hour == 0:
                base_time = "2330"
                base_date = (now - timedelta(days=1)).strftime('%Y%m%d')
            else:
                base_time = (now - timedelta(hours=1)).strftime('%H') + "30"
        else:
            base_time = now.strftime('%H') + "30"
        return base_date, base_time












    def display_image(self, image_path):
        if not self.is_preview_mode and not self.epd: 
            # If no EPD but not in preview mode, we might be testing.
            pass

        try:
            logger.info(f"Processing: {os.path.basename(image_path)}")

            # 데이터 로드
            d_data = self.get_fine_dust_data()
            w_data = self.get_weather_data()
            
            # 설정 및 위치 이름 로드
            layout_config = self.config.get('layout', {})
            location_name = self.config.get('location', {}).get('name', '')

            # [핵심] Renderer 모듈 사용 (Web Preview와 동일한 로직)
            final_img, _, _, _, _ = renderer.create_composed_image(
                image_path, 
                w_data, 
                d_data, 
                layout_config, 
                location_name
            )

            # [중요] 웹 미리보기 저장
            preview_path = settings.PREVIEW_PATH
            os.makedirs(os.path.dirname(preview_path), exist_ok=True)
            final_img.save(preview_path)
            logger.info(f"Preview Saved: {preview_path}")

            if self.is_preview_mode: 
                return

            # E-Ink 전송
            if self.epd:
                logger.info("Updating E-Ink...")
                try:
                    self.epd.init()
                    final_quantized = final_img.quantize(palette=self.get_7color_palette(), method=Image.FLOYDSTEINBERG)
                    self.epd.display(self.epd.getbuffer(final_quantized))
                    self.epd.sleep()
                    logger.info("Done.")
                except Exception as e:
                    logger.error(f"EPD Error: {e}")

        except Exception as e:
            logger.error(f"Display Error: {e}", exc_info=True)

    # --- Power Management ---
    def is_charging(self):
        """PiSugar 서버에 접속해 현재 충전기(전원)가 연결되어 있는지 확인"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect(('127.0.0.1', 8423))
                s.sendall(b'get battery')
                data = s.recv(1024).decode('utf-8')
                if '"charging":true' in data.replace(" ", ""):
                    return True
        except Exception as e:
            # logger.warning(f"PiSugar check failed: {e}")
            pass
        return False

    def refresh_display(self):
        """Alias for standard run/update used by app.py"""
        self.config = settings.load_config() # Reload latest config
        
        # Support Selected Photo Logic
        pinned_photo = self.config.get('selected_photo')
        selected_photo = None
        
        if pinned_photo:
            full_path = os.path.join(self.photos_dir, pinned_photo)
            logger.info(f"Checking pinned photo path: {full_path}")
            if os.path.exists(full_path):
                selected_photo = full_path
                logger.info(f"✅ Found pinned photo: {full_path}")
            else:
                # Try checking if it's just a filename that needs to be found in uploads
                # Sometimes path might be mixed up
                logger.warning(f"❌ Pinned photo NOT found at: {full_path}")
                
        if not selected_photo:
            # Fallback logic
            pass
            
        # [Shuffle Logic]
        shuffle_mode = self.config.get('shuffle_mode', False)
        shuffle_playlist = self.config.get('shuffle_playlist', [])
        
        if shuffle_mode:
            logger.info("🔀 Shuffle Mode Enabled")
            # Filter playlist for existing files
            valid_playlist = []
            for p in shuffle_playlist:
                full_p = os.path.join(self.photos_dir, p)
                if os.path.exists(full_p):
                    valid_playlist.append(full_p)
            
            if valid_playlist:
                selected_photo = random.choice(valid_playlist)
                logger.info(f"🎲 Randomly selected from playlist: {os.path.basename(selected_photo)}")
            else:
                logger.warning("Shuffle playlist empty or files missing. Falling back to all photos.")
                all_photos = self.get_photo_list()
                if all_photos:
                    selected_photo = random.choice(all_photos)
        
        # If shuffle is OFF, check if we have a pinned photo (Already checked above)
        elif not selected_photo:
             # Standard fallback if no pinned photo
            photos = self.get_photo_list()
            if photos:
                selected_photo = random.choice(photos)
        
        if selected_photo:
            logger.info(f"Final selected photo: {selected_photo}")
            self.display_image(selected_photo)
        else:
            logger.warning("No photos to display.")

    def run(self):
        """메인 실행 로직 (Standalone)"""
        if not self.init_display(): return

        self.refresh_display()

        if self.is_preview_mode:
            logger.info("미리보기 모드: 시스템을 종료하지 않습니다.")
            return

        if self.is_charging():
            logger.info("⚡ 전원 케이블 연결됨 감지! 웹 서버 실행.")
            try:
                # Use absolute path for app.py
                app_path = os.path.join(settings.BASE_DIR, 'app.py')
                os.system(f"nohup python3 {app_path} > /dev/null 2>&1 &")
            except Exception as e:
                logger.error(f"웹 서버 실행 실패: {e}")
            return

        logger.info("🔋 배터리 모드: 5초 후 시스템을 안전하게 종료합니다 (PiSugar).")
        time.sleep(5)
        os.system("sudo shutdown now")

if __name__ == "__main__":
    try:
        EInkPhotoFrame().run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.critical(f"Critical Error: {e}", exc_info=True)
