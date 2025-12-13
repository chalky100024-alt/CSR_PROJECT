from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Constants
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480

def get_font_path(bold=True):
    # This might need to be adjusted or we can pass font paths in
    # For now, we reuse the logic or hardcode paths relative to project
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Fonts from user reference
    fonts = [
        # Local Project Root (Best Match)
        os.path.join(base_dir, "AppleSDGothicNeoB.ttf"), 
        # User specific local paths
        "/usr/local/share/fonts/apple_sandol/AppleSDGothicNeoEB.ttf" if bold else "/usr/local/share/fonts/apple_sandol/AppleSDGothicNeoB.ttf",
        "/usr/local/share/fonts/apple_sandol/AppleSDGothicNeoM.ttf",
        # Project local fallback (User's subdir)
        os.path.join(base_dir, "Apple_산돌고딕_Neo", "AppleSDGothicNeoEB.ttf" if bold else "AppleSDGothicNeoB.ttf"),
        # Standard System Fonts
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf" if bold else "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         # Generic Fallbacks
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
    ]
    for f in fonts:
        if os.path.exists(f): return f
    return None

def get_font(size=20, bold=True):
    path = get_font_path(bold)
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def resize_image_fill(image, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT):
    target_ratio = width / height
    img_ratio = image.width / image.height
    
    if img_ratio > target_ratio:
        # Image is wider than display: Resize by height, crop width
        new_height = height
        new_width = int(image.width * (new_height / image.height))
    else:
        # Image is taller than display: Resize by width, crop height
        new_width = width
        new_height = int(image.height * (new_width / image.width))
        
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Simple Center Crop
    left = (new_width - width) / 2
    top = (new_height - height) / 2
    
    return resized.crop((left, top, left + width, top + height))

def enhance_image(image):
    if image.mode != 'RGB': image = image.convert('RGB')
    image = ImageEnhance.Contrast(image).enhance(1.2)
    image = ImageEnhance.Sharpness(image).enhance(1.5)
    return ImageEnhance.Color(image).enhance(1.1)

def get_dust_grade_info(pm10, pm25):
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

def _load_weather_icons(icon_dir):
    icons = {}
    icon_map = {'맑음': 'sun.png', '구름 많음': 'cloud.png', '흐림': 'cloudy.png', '비': 'rain.png',
                '비 또는 눈': 'rain_snow.png', '눈': 'snow.png', '소나기': 'shower.png', '정보없음': 'unknown.png'}
    if not os.path.exists(icon_dir): return icons
    for desc, filename in icon_map.items():
        path = os.path.join(icon_dir, filename)
        if os.path.exists(path):
            try:
                icons[desc] = Image.open(path).convert("RGBA").resize((45, 45), Image.Resampling.LANCZOS)
            except:
                pass
    return icons

def create_composed_image(image_path, weather_data, dust_data, layout_config=None, location_name=""):
    # Defaults
    if layout_config is None: layout_config = {}
    
    # Load Image
    try:
        if image_path and os.path.exists(image_path):
            img = Image.open(image_path)
        else:
            img = Image.new('RGB', (DISPLAY_WIDTH, DISPLAY_HEIGHT), (200, 200, 200))
    except:
        img = Image.new('RGB', (DISPLAY_WIDTH, DISPLAY_HEIGHT), (200, 200, 200))
        
    img = resize_image_fill(img)
    img = enhance_image(img)
    
    # Overlay
    overlay = Image.new('RGBA', (DISPLAY_WIDTH, DISPLAY_HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    # --- [Apple-like Vertical Widget Layout] ---
    # Apply defaults if missing
    widget_scale = float(layout_config.get('widget_size', 1.0))
    opacity_val = float(layout_config.get('opacity', 0.85)) # Higher default
    bg_alpha = int(255 * opacity_val)

    # Base Dimensions
    card_w = int(200 * widget_scale) 
    card_h = int(220 * widget_scale) # Initial estimate
    padding = int(15 * widget_scale)
    line_spacing = int(5 * widget_scale)

    # Fonts
    # renderer.py uses global get_font function
    font_xl = get_font(int(40 * widget_scale)) 
    font_lg = get_font(int(22 * widget_scale)) 
    font_md = get_font(int(18 * widget_scale)) 
    font_sm = get_font(int(14 * widget_scale)) 

    # Data Preparation
    temp_str = "--°"
    desc_str = ""
    rain_str = ""
    w_icon = None

    if weather_data and 'temp' in weather_data:
        temp_str = f"{int(weather_data['temp'])}°"
        desc_str = weather_data.get('weather_description', '정보없음')
        
        # Icon
        w_icon = weather_icons.get(desc_str, weather_icons.get('정보없음'))
        
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
    if dust_data:
        grade, sym, color = get_dust_grade_info(dust_data.get('pm10'), dust_data.get('pm25'))
        dust_str = f"미세먼지 {grade}"
        dust_color = color
    else:
        dust_str = "미세먼지 정보 없음"

    # Time
    time_str = datetime.now().strftime('%m/%d %H:%M')

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

    box_h = int(current_y) # Update height
    box_w = card_w

    # Position Logic
    pos_x = layout_config.get('x')
    pos_y = layout_config.get('y')
    layout_type = layout_config.get('type')
    
    box_x = DISPLAY_WIDTH - box_w - int(20 * widget_scale) # Default Right
    box_y = int(20 * widget_scale) # Default Top

    if layout_type == 'custom':
        if pos_x is not None: box_x = int(float(pos_x))
        if pos_y is not None: box_y = int(float(pos_y))
    elif layout_config.get('position') == 'bottom' or layout_type == 'type_B':
         box_y = DISPLAY_HEIGHT - box_h - int(20 * widget_scale)

    # Overflow Protection
    if box_x + box_w > DISPLAY_WIDTH: box_x = DISPLAY_WIDTH - box_w - 5
    if box_x < 0: box_x = 0
    if box_y + box_h > DISPLAY_HEIGHT: box_y = DISPLAY_HEIGHT - box_h - 5
    if box_y < 0: box_y = 0

    # Draw Background (Rounded Card)
    draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], 
                           radius=int(20 * widget_scale), 
                           fill=(255, 255, 255, bg_alpha), 
                           outline=None)
    
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

    # Row 5: Time (Bottom)
    draw.text((cx + 5, cy), time_str, font=font_sm, fill=(100,100,100))

    final_image = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    return final_image, box_x, box_y, box_w, box_h
