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
            os.path.join(BASE_DIR, "AppleSDGothicNeoB.ttf"), # Downloaded Fallback
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

    def get_fine_dust_data(self):
        if not self.airkorea_api_key: return None
        url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty"
        params = {'serviceKey': self.airkorea_api_key, 'returnType': 'json', 'numOfRows': '1', 'pageNo': '1',
                  'stationName': self.station_name, 'dataTerm': 'DAILY', 'ver': '1.3'}
        try:
            res = requests.get(url, params=params, timeout=10)
            items = res.json().get('response', {}).get('body', {}).get('items', [])
            if items:
                return {'pm10': int(items[0]['pm10Value']), 'pm25': int(items[0]['pm25Value']),
                        'time': items[0]['dataTime']}
        except:
            pass
        return None

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

    def get_weather_data(self):
        if not self.kma_weather_api_key: return None
        weather_info = {}
        try:
            # 1. 초단기실황
            bd, bt = self.get_kma_base_time('ultrasrt')
            url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
            params = {'serviceKey': self.kma_weather_api_key, 'numOfRows': '10', 'pageNo': '1',
                      'base_date': bd, 'base_time': bt, 'nx': self.kma_nx, 'ny': self.kma_ny, '_type': 'xml'}

            root = ET.fromstring(requests.get(url, params=params, timeout=10).text)
            for item in root.findall(".//item"):
                cat = item.find("category").text
                val = item.find("obsrValue").text
                if cat == 'T1H':
                    weather_info['temp'] = _safe_float(val)
                elif cat == 'RN1':
                    weather_info['current_rain_amount'] = _safe_float(val)

            # 2. 초단기예보
            bd, bt = self.get_kma_base_time('ultrasrt_fcst')
            url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"
            params['base_date'] = bd;
            params['base_time'] = bt;
            params['numOfRows'] = '60'

            root = ET.fromstring(requests.get(url, params=params, timeout=10).text)
            forecasts = {}
            for item in root.findall(".//item"):
                dt = item.find("fcstDate").text + item.find("fcstTime").text
                if dt not in forecasts: forecasts[dt] = {}
                forecasts[dt][item.find("category").text] = item.find("fcstValue").text

            now = datetime.now()
            closest_time = min(
                [t for t in forecasts.keys() if datetime.strptime(t, '%Y%m%d%H%M') >= now - timedelta(minutes=30)],
                key=lambda x: abs(datetime.strptime(x, '%Y%m%d%H%M') - now), default=None)

            if closest_time:
                sky = int(forecasts[closest_time].get('SKY', '1'))
                pty = int(forecasts[closest_time].get('PTY', '0'))
                weather_info['weather_main_code'] = pty
                if pty == 0:
                    weather_info['weather_description'] = ['맑음', '맑음', '구름 많음', '흐림'][sky - 1] if sky <= 4 else '흐림'
                else:
                    weather_info['weather_description'] = ['', '비', '비 또는 눈', '눈', '소나기'][pty]

            # 6시간 강수 예보
            max_rain = None
            for t in sorted(forecasts.keys()):
                ft = datetime.strptime(t, '%Y%m%d%H%M')
                if now <= ft <= now + timedelta(hours=6):
                    pty = int(forecasts[t].get('PTY', '0'))
                    rn1 = _safe_float(forecasts[t].get('RN1', '0'))
                    if pty > 0 and rn1 > 0:
                        if not max_rain or rn1 > max_rain['amount']:
                            max_rain = {'amount': rn1, 'start_time': ft.strftime('%H:%M'),
                                        'end_time': (ft + timedelta(hours=1)).strftime('%H:%M'), 'type_code': pty}
            weather_info['rain_forecast'] = max_rain
            return weather_info
        except Exception as e:
            logger.error(f"Weather API Error: {e}")
            return None

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

        # --- [Layout Configuration] ---
        layout_cfg = self.config.get('layout', {})
        widget_scale = float(layout_cfg.get('widget_size', 1.0))
        opacity_val = float(layout_cfg.get('opacity', 0.6)) # Default 0.6
        bg_alpha = int(255 * (1.0 - opacity_val)) # Invert logic: opacity 0.3 means 30% visible? 
        # Usually "opacity" in UI means "transparency of background" or "alpha value".
        # Let's assume opacity 1.0 = Fully Opaque, 0.0 = Fully Transparent.
        bg_alpha = int(255 * opacity_val) 

        # Base font sizes scaled by widget_size
        base_lg = int(23 * widget_scale)
        base_md = int(20 * widget_scale)
        base_sm = int(18 * widget_scale)
        base_dt = int(12 * widget_scale)

        font_lg = self.get_font(base_lg)
        font_md = self.get_font(base_md)
        font_sm = self.get_font(base_sm)
        font_dt = self.get_font(base_dt)

        lines = []
        w_icon = None

        # 1. 날씨 라인 구성
        if weather_data and 'temp' in weather_data:
            desc = weather_data.get('weather_description', '정보없음')
            if desc in self.weather_icons:
                w_icon = self.weather_icons[desc]
                # Scale icon too
                target_icon_size = int(45 * widget_scale)
                if w_icon.size[0] != target_icon_size:
                     w_icon = w_icon.resize((target_icon_size, target_icon_size), Image.Resampling.LANCZOS)
            else:
                w_icon = self.weather_icons.get('정보없음')
                if w_icon:
                    target_icon_size = int(45 * widget_scale)
                    w_icon = w_icon.resize((target_icon_size, target_icon_size), Image.Resampling.LANCZOS)

            lines.append(f"{weather_data['temp']:.1f}°C ({desc})")

            if weather_data.get('rain_forecast'):
                rf = weather_data['rain_forecast']
                rtype = ["", "비", "비/눈", "눈", "소나기"][rf['type_code']]
                lines.append(f"└ {rtype} {rf['start_time']}~ {rf['amount']:.1f}mm")
            elif weather_data.get('current_rain_amount', 0) > 0:
                lines.append(f"└ 현재 강수량: {weather_data['current_rain_amount']:.1f}mm")
        else:
            lines.append("날씨 정보 없음")
            w_icon = self.weather_icons.get('정보없음')
            if w_icon:
                target_icon_size = int(45 * widget_scale)
                w_icon = w_icon.resize((target_icon_size, target_icon_size), Image.Resampling.LANCZOS)

        # 2. 미세먼지 라인 구성
        # Color state
        self.dust_color = (128, 128, 128)
        
        if dust_data:
            grade, sym, color = self.get_dust_grade_info(dust_data.get('pm10'), dust_data.get('pm25'))
            lines.append(f"{sym} {grade} (PM10:{dust_data['pm10']}|PM2.5:{dust_data['pm25']})")
            self.dust_color = color
        else:
            lines.append("미세먼지 정보 없음")

        lines.append(datetime.now().strftime('%m/%d %H시 기준'))

        # --- [레이아웃 계산] ---
        pad = int(5 * widget_scale)
        line_heights = [font_lg.getmetrics()[0] + font_lg.getmetrics()[1] for _ in lines]
        
        total_h = sum(line_heights) + (pad * len(lines)) + int(30 * widget_scale)
        
        try:
            icon_w = w_icon.width if w_icon else 0
            max_text_w = max([draw.textlength(l, font_lg) for l in lines]) 
            max_w = max_text_w + icon_w + int(20 * widget_scale)
        except:
             max_w = int(300 * widget_scale)

        box_w, box_h = max_w + int(30 * widget_scale), total_h + int(20 * widget_scale)
        margin = int(15 * widget_scale)

        # Position Logic
        pos = layout_cfg.get('position', 'top')
        layout_type = layout_cfg.get('type', 'type_A')
        
        # Default X (Right Aligned)
        box_x = self.display_width - box_w - margin

        # Y Position
        if layout_type == 'custom':
            # Use specific x/y if available, else default
            try:
                box_x = int(layout_cfg.get('x', box_x))
                box_y = int(layout_cfg.get('y', margin))
            except:
                box_y = margin
        elif pos == 'bottom' or layout_type == 'type_B':
            box_y = self.display_height - box_h - margin
        else:
            box_y = margin

        # 박스 그리기
        draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=10, fill=(255, 255, 255, bg_alpha),
                               outline=(0, 0, 0), width=2)

        # 텍스트 그리기
        cy = box_y + int(15 * widget_scale)
        cx = box_x + int(15 * widget_scale)

        # 첫째줄 (날씨)
        if w_icon:
            overlay.paste(w_icon, (int(cx), int(cy)), w_icon)
            cx += w_icon.width + int(5 * widget_scale)
        draw.text((cx, cy), lines[0], font=font_lg, fill=(0, 0, 0))
        cy += line_heights[0] + pad # Move down
        cx = box_x + int(15 * widget_scale)

        # 나머지 줄
        for i, line in enumerate(lines[1:]):
            f = font_dt if i == len(lines) - 2 else font_md # Last line is date (small)
            if "●" in line:  # 미세먼지 줄
                parts = line.split(' ', 1)
                sym = parts[0]
                txt = parts[1] if len(parts) > 1 else ""
                
                draw.text((cx, cy), sym, font=f, fill=self.dust_color)
                draw.text((cx + draw.textlength(sym, f) + 5, cy), txt, font=f, fill=(0, 0, 0))
            else:
                draw.text((cx, cy), line, font=f, fill=(0, 0, 0))
            cy += line_heights[i + 1] + pad

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
