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
        self.weather_icons = self._load_weather_icons()

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

    def _load_weather_icons(self):
        icons = {}
        icon_map = {'맑음': 'sun.png', '구름 많음': 'cloud.png', '흐림': 'cloudy.png', '비': 'rain.png',
                    '비 또는 눈': 'rain_snow.png', '눈': 'snow.png', '소나기': 'shower.png', '정보없음': 'unknown.png'}
        if not os.path.exists(self.icon_dir): return icons
        for desc, filename in icon_map.items():
            path = os.path.join(self.icon_dir, filename)
            if os.path.exists(path):
                try:
                    icons[desc] = Image.open(path).convert("RGBA").resize((45, 45), Image.Resampling.LANCZOS)
                except:
                    pass
        return icons

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

    def enhance_image(self, image):
        if image.mode != 'RGB': image = image.convert('RGB')
        image = ImageEnhance.Contrast(image).enhance(1.2)
        image = ImageEnhance.Sharpness(image).enhance(1.5)
        return ImageEnhance.Color(image).enhance(1.1)



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



    def get_font(self, size=20):
        for font_path in self.font_paths:
            if os.path.exists(font_path): return ImageFont.truetype(font_path, size)
        return ImageFont.load_default()

    def resize_image_fill(self, image):
        target_ratio = self.display_width / self.display_height
        img_ratio = image.width / image.height
        if img_ratio > target_ratio:
            new_height = self.display_height
            new_width = int(image.width * (new_height / image.height))
        else:
            new_width = self.display_width
            new_height = int(image.height * (new_width / image.width))
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        left = (new_width - self.display_width) / 2
        top = (new_height - self.display_height) / 2
        return resized.crop((left, top, left + self.display_width, top + self.display_height))

    def get_dust_grade_info(self, pm10, pm25):
        try:
            p10, p25 = int(pm10 or -1), int(pm25 or -1)
        except:
            return "정보 없음", "●", (128, 128, 128)

        lv = max(
            1 if p25 <= 15 else 2 if p25 <= 35 else 3 if p25 <= 75 else 4,
            1 if p10 <= 30 else 2 if p10 <= 80 else 3 if p10 <= 150 else 4
        )
        return ["", "좋음", "보통", "나쁨", "매우나쁨"][lv], "●", \
        [(0, 0, 0), (0, 0, 255), (0, 128, 0), (255, 165, 0), (255, 0, 0)][lv]

    def create_info_overlay_image(self, dust_data, weather_data):
        overlay = Image.new('RGBA', (self.display_width, self.display_height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        # --- [Apple-like Vertical Widget Layout] ---
        layout_cfg = self.config.get('layout', {})
        widget_scale = float(layout_cfg.get('widget_size', 1.0))
        opacity_val = float(layout_cfg.get('opacity', 0.85)) # Higher default for card look
        bg_alpha = int(255 * opacity_val)

        # Base Dimensions
        # Fixed width for consistent look (Apple Widget style)
        card_w = int(200 * widget_scale) 
        card_h = int(220 * widget_scale) # Initial estimate, will adjust
        padding = int(15 * widget_scale)
        line_spacing = int(5 * widget_scale)

        # Fonts
        font_xl = self.get_font(int(40 * widget_scale)) # Temp
        font_lg = self.get_font(int(22 * widget_scale)) # Main Text
        font_md = self.get_font(int(18 * widget_scale)) # Sub Text
        font_sm = self.get_font(int(14 * widget_scale)) # Detail/Time

        # Data Preparation
        temp_str = "--°"
        desc_str = ""
        rain_str = ""
        w_icon = None

        if weather_data and 'temp' in weather_data:
            temp_str = f"{int(weather_data['temp'])}°"
            desc_str = weather_data.get('weather_description', '정보없음')
            
            # Icon
            if desc_str in self.weather_icons:
                w_icon = self.weather_icons[desc_str]
            else:
                w_icon = self.weather_icons.get('정보없음')
            
            if w_icon:
                # Icon size
                icon_sz = int(50 * widget_scale)
                if w_icon.size[0] != icon_sz:
                    w_icon = w_icon.resize((icon_sz, icon_sz), Image.Resampling.LANCZOS)

            # Rain
            if weather_data.get('rain_forecast'):
                rf = weather_data['rain_forecast']
                rtype = ["", "비", "비/눈", "눈", "소나기"][rf['type_code']]
                rain_str = f"{rtype} {rf['amount']:.1f}mm"
            elif weather_data.get('current_rain_amount', 0) > 0:
                rain_str = f"강수 {weather_data['current_rain_amount']:.1f}mm"
        
        # Dust
        dust_str = ""
        dust_color = (100, 100, 100)
        dust_grade = ""
        if dust_data:
            grade, sym, color = self.get_dust_grade_info(dust_data.get('pm10'), dust_data.get('pm25'))
            dust_str = f"미세먼지 {grade}"
            dust_grade = grade
            dust_color = color
        else:
            dust_str = "미세먼지 정보 없음"

        # Time
        time_str = datetime.now().strftime('%m/%d %H:%M')

        # --- Calculate Dynamic Height if needed, or stick to fixed ---
        # Let's do a vertical stack
        # Row 1: Icon (Left) + Temp (Right)
        # Row 2: Desc (Small)
        # Divider
        # Row 3: Rain (if exists)
        # Row 4: Dust
        # Row 5: Time (Bottom)

        # Calculate Box Height dynamically
        current_y = padding
        
        # Row 1 Height (Max of Icon or Temp)
        row1_h = max(w_icon.height if w_icon else 0, font_xl.getbbox(temp_str)[3])
        current_y += row1_h + line_spacing
        
        # Row 2 (Desc)
        current_y += font_md.getbbox(desc_str)[3] + (line_spacing * 2)
        
        # Row 3 (Rain)
        if rain_str:
            current_y += font_md.getbbox(rain_str)[3] + line_spacing

        # Row 4 (Dust)
        current_y += font_md.getbbox(dust_str)[3] + line_spacing
        
        # Row 5 (Time) - margin top
        current_y += 10 + font_sm.getbbox(time_str)[3] + padding

        card_h = int(current_y) # Update height

        # --- Positioning ---
        # Default Right-Top or User Config
        pos = layout_cfg.get('position', 'top')
        layout_type = layout_cfg.get('type', 'type_A')
        
        box_x = self.display_width - card_w - int(20 * widget_scale) # Default Right
        box_y = int(20 * widget_scale) # Default Top

        if layout_type == 'custom':
            try:
                box_x = int(layout_cfg.get('x', box_x))
                box_y = int(layout_cfg.get('y', box_y))
            except: pass
        elif pos == 'bottom' or layout_type == 'type_B':
            box_y = self.display_height - card_h - int(20 * widget_scale)
        
        # Overflow Protection
        if box_x + card_w > self.display_width: box_x = self.display_width - card_w - 5
        if box_x < 0: box_x = 0
        if box_y + card_h > self.display_height: box_y = self.display_height - card_h - 5
        if box_y < 0: box_y = 0

        # Draw Background (Rounded Card)
        draw.rounded_rectangle([box_x, box_y, box_x + card_w, box_y + card_h], 
                               radius=int(20 * widget_scale), 
                               fill=(255, 255, 255, bg_alpha), 
                               outline=None) # No border for cleaner look, or subtle gray
        
        # Content Draw Cursor
        cx = box_x + padding
        cy = box_y + padding

        # Row 1: Icon & Temp
        if w_icon:
            overlay.paste(w_icon, (cx, cy), w_icon)
            # Temp Text right next to icon
            temp_x = cx + w_icon.width + 10
            # Center vertically with icon
            temp_y = cy + (w_icon.height - font_xl.getbbox(temp_str)[3]) // 2 - 5
            draw.text((temp_x, temp_y), temp_str, font=font_xl, fill=(0,0,0))
            cy += max(w_icon.height, font_xl.getbbox(temp_str)[3]) + line_spacing
        else:
            draw.text((cx, cy), temp_str, font=font_xl, fill=(0,0,0))
            cy += font_xl.getbbox(temp_str)[3] + line_spacing

        # Row 2: Desc
        draw.text((cx + 5, cy), desc_str, font=font_md, fill=(60,60,60))
        cy += font_md.getbbox(desc_str)[3] + (line_spacing * 2)

        # Row 3: Rain (Optional)
        if rain_str:
            draw.text((cx + 5, cy), f"☔ {rain_str}", font=font_md, fill=(0,0,200))
            cy += font_md.getbbox(rain_str)[3] + line_spacing

        # Row 4: Dust
        # Draw colored dot + text
        dot_r = 4
        dot_y = cy + 10
        draw.ellipse([cx + 5, dot_y - dot_r, cx + 5 + (dot_r*2), dot_y + dot_r], fill=dust_color)
        draw.text((cx + 20, cy), dust_str, font=font_md, fill=(0,0,0))
        cy += font_md.getbbox(dust_str)[3] + line_spacing + 10

        # Row 5: Time (Bottom, Right-aligned or Left)
        draw.text((cx + 5, cy), time_str, font=font_sm, fill=(100,100,100))

        return overlay

    def display_image(self, image_path):
        if not self.is_preview_mode and not self.epd: 
            # If no EPD but not in preview mode, we might be testing.
            # But earlier logic says "If !HAS_EPD -> Preview Mode" implicitly or just logs error.
            # We continue to generate preview.jpg at least.
            pass

        try:
            logger.info(f"Processing: {os.path.basename(image_path)}")

            # 이미지 처리
            img = Image.open(image_path)
            img = self.resize_image_fill(img)
            img = self.enhance_image(img)

            # 오버레이 합성
            d_data = self.get_fine_dust_data()
            w_data = self.get_weather_data()
            overlay = self.create_info_overlay_image(d_data, w_data)

            final_img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

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
                
        if not selected_photo:
            photos = self.get_photo_list()
            if photos:
                # Default to random or latest? User code used random.
                # Project standard usually prefers latest.
                # Let's stick to User's Random choice if untethered, 
                # but App usually sets selected_photo if user clicks a file.
                # If specific photo not selected, random is nice for a frame.
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
