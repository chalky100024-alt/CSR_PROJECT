#!/usr/bin/env python3
import os
import sys
import time
import random
import logging
import settings
import data_api
import renderer
import hardware
from PIL import Image

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Waveshare Check
try:
    from waveshare_epd import epd7in3f
    HAS_EPD = True
except ImportError:
    HAS_EPD = False

class EInkPhotoFrame:
    def __init__(self):
        self.config = settings.load_config()
        self.hw = hardware.HardwareController()
        
        self.api_key_air = self.config.get('api_key_air', "")
        self.api_key_kma = self.config.get('api_key_kma', "")
        self.station_name = self.config.get('station_name', "고덕")
        location = self.config.get('location', {})
        self.nx = int(location.get('nx', 61))
        self.ny = int(location.get('ny', 115))
        
        # Check command line for preview
        self.is_preview_mode = ('--preview' in sys.argv)
        
    def get_7color_palette(self):
        standard_7_colors = [0, 0, 0, 255, 255, 255, 255, 0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 0, 255, 165, 0]
        filler = [255, 255, 255]
        full_palette_data = standard_7_colors + filler * (256 - len(standard_7_colors) // 3)
        palette_image = Image.new('P', (1, 1), 0)
        palette_image.putpalette(full_palette_data[:768])
        return palette_image

    def run(self):
        # 1. Init Display (via Hardware Controller if needed, or direct)
        # Using hardware.py abstraction or direct usage? 
        # User snippet used direct usage. hardware.py acts as wrapper.
        # Let's use hardware.py for consistency.
        
        # 2. Photos
        if not os.path.exists(settings.UPLOADS_DIR):
            os.makedirs(settings.UPLOADS_DIR)
        
        photos = [os.path.join(settings.UPLOADS_DIR, f) for f in os.listdir(settings.UPLOADS_DIR) 
                  if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        
        selected_photo = random.choice(photos) if photos else None
        
        # 3. Fetch Data
        w_data = data_api.get_weather_data(self.api_key_kma, self.nx, self.ny)
        d_data = data_api.get_fine_dust_data(self.api_key_air, self.station_name)
        
        # 4. Render
        # 4. Render
        layout = self.config.get('layout', {})
        location_name = self.config.get('location', {}).get('name', '')
        final_img, _, _, _, _ = renderer.create_composed_image(selected_photo, w_data, d_data, layout, location_name)
        
        # Save Preview
        try:
            os.makedirs(os.path.dirname(settings.PREVIEW_PATH), exist_ok=True)
            final_img.save(settings.PREVIEW_PATH)
            logger.info(f"Preview Saved: {settings.PREVIEW_PATH}")
        except Exception as e:
            logger.error(f"Preview Save Error: {e}")

        if self.is_preview_mode:
            logger.info("Preview Mode: No E-Ink update.")
            return

        # 5. Check Power & Branch
        if self.hw.is_charging():
            logger.info("⚡ Charging detected. Starting Web Server...")
            # Use sys.executable to ensure we use the same venv
            cmd = f"nohup {sys.executable} {os.path.join(settings.BASE_DIR, 'app.py')} > /dev/null 2>&1 &"
            os.system(cmd)
            return

        # 6. Display on E-Ink
        logger.info("Updating E-Ink...")
        # To match user snippet's dithering logic:
        if HAS_EPD and self.hw.epd: # hw.epd might be None if mock
             # Dithering
            final_quantized = final_img.quantize(palette=self.get_7color_palette(), method=Image.FLOYDSTEINBERG)
            self.hw.epd.init()
            self.hw.epd.display(self.hw.epd.getbuffer(final_quantized))
            self.hw.epd.sleep()
        else:
            self.hw.display_image(final_img) # Mock or fallback

        logger.info("Shutdown sequence initiated.")
        time.sleep(5)
        # os.system("sudo shutdown now")

if __name__ == "__main__":
    try:
        EInkPhotoFrame().run()
    except Exception as e:
        logger.critical(f"Critical Error: {e}", exc_info=True)
