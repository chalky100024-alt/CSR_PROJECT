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
import threading
from PIL import Image

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Waveshare import removed - use hardware.py instead


class EInkPhotoFrame:
    def __init__(self):
        self.config = settings.load_config()
        self.hw = hardware.HardwareController()
        
        self.api_key_air = self.config.get('api_key_air', "")
        self.api_key_kma = self.config.get('api_key_kma', "")
        loc_name = self.config.get('location', {}).get('name', '')
        if loc_name:
            self.station_name = loc_name.split()[-1]
        else:
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

    # Global Lock for display updates to prevent overlapping
    _lock = threading.Lock()

    def refresh_display(self):
        """Force refresh the E-Ink display with current settings/photo."""
        if not self._lock.acquire(blocking=False):
            logger.warning("Display refresh already in progress. Skipping this request.")
            return False
            
        try:
            logger.info("Starting Display Refresh...")
            
            # Reload config to get latest updates
            self.config = settings.load_config()
            
            # 1. Photos
            if not os.path.exists(settings.UPLOADS_DIR):
                os.makedirs(settings.UPLOADS_DIR)
            
            photos = [os.path.join(settings.UPLOADS_DIR, f) for f in os.listdir(settings.UPLOADS_DIR) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
            
            if not photos:
                logger.warning("No photos found.")
                return False
                
            # Check if a specific photo is fixed in config
            pinned_photo = self.config.get('selected_photo')
            selected_photo = None
            
            if pinned_photo:
                full_path = os.path.join(settings.UPLOADS_DIR, pinned_photo)
                if os.path.exists(full_path):
                    selected_photo = full_path
                    logger.info(f"Selected pinned photo: {pinned_photo}")
                else:
                    logger.warning(f"Pinned photo not found: {full_path}")
            
            if not selected_photo:
                # Fallback: Sort by modification time (Newest first)
                photos.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                selected_photo = photos[0]
                logger.info(f"Fallback to latest photo: {os.path.basename(selected_photo)}")
            
            # 2. Fetch Data (Blocking with Timeout)
            # User requested to ensure data is received before displaying
            w_data = None
            d_data = None
            
            max_retries = 10 # 10 * 2sec = 20 seconds max wait
            for i in range(max_retries):
                logger.info(f"Fetching data attempt {i+1}/{max_retries}...")
                
                if w_data is None: 
                    w_data = data_api.get_weather_data(self.api_key_kma, self.nx, self.ny)
                
                if d_data is None: 
                    d_data = data_api.get_fine_dust_data(self.api_key_air, self.station_name)
                
                # If we have both (or at least one if the other is failing hard?), break
                # For now, strict: wait for both unless retries exhausted
                if w_data and d_data: 
                    logger.info("Data fetch complete.")
                    break
                    
                time.sleep(2)
                
            if not w_data: logger.warning("Weather data fetch failed after retries.")
            if not d_data: logger.warning("Dust data fetch failed after retries.")
            
            # 3. Render
            layout = self.config.get('layout', {})
            location_name = self.config.get('location', {}).get('name', '')
            final_img, _, _, _, _ = renderer.create_composed_image(selected_photo, w_data, d_data, layout, location_name)
            
            # 4. Dithering & Display
            # Use hardware controller's EPD instance
            if self.hw.epd:
                logger.info("Initializing EPD and displaying...")
                try:
                    self.hw.epd.init()
                    # 7-Color Dithering
                    final_quantized = final_img.quantize(palette=self.get_7color_palette(), method=Image.FLOYDSTEINBERG)
                    self.hw.epd.display(self.hw.epd.getbuffer(final_quantized))
                    self.hw.epd.sleep()
                    logger.info("Display update successful.")
                except Exception as e:
                    logger.error(f"EPD Error: {e}")
                    return False
            else:
                self.hw.display_image(final_img) # Mock/PC fallback
                logger.info("Mock Display Update.")
                
            return True
    
    finally:
        self._lock.release()

    def run(self):
        # ... Legacy run behavior if needed for standalone execution ...
        # For now, we just call refresh
        self.refresh_display()
        
        # 5. Check Power & Branch (Only relevant if running as standalone script)
        if self.hw.is_charging():
           # ... start server logic ...
           pass

if __name__ == "__main__":
    try:
        EInkPhotoFrame().run()
    except Exception as e:
        logger.critical(f"Critical Error: {e}", exc_info=True)
