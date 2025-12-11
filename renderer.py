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
        # User specific local paths
        "/usr/local/share/fonts/apple_sandol/AppleSDGothicNeoEB.ttf" if bold else "/usr/local/share/fonts/apple_sandol/AppleSDGothicNeoB.ttf",
        "/usr/local/share/fonts/apple_sandol/AppleSDGothicNeoM.ttf",
        # Project local fallback
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

    # Layout Config
    try:
        base_font_size = int(layout_config.get('font_size', 20))
        scale = float(layout_config.get('widget_size', 1.0))
        opacity = float(layout_config.get('opacity', 0.6))
    except:
        base_font_size = 20
        scale = 1.0
        opacity = 0.6
    
    # Apply scale to font size
    font_sm = get_font(int(base_font_size * 0.9 * scale))
    font_md = get_font(int(base_font_size * 1.0 * scale))
    font_lg = get_font(int(base_font_size * 1.15 * scale))
    font_dt = get_font(int(base_font_size * 0.6 * scale))

    # Load Icons (Assuming icons dir is relative to project root)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_dir = os.path.join(base_dir, 'icons')
    weather_icons = _load_weather_icons(icon_dir)

    lines = []
    w_icon = None

    # 1. Weather Line
    if weather_data and 'temp' in weather_data:
        desc = weather_data.get('weather_description', '정보없음')
        w_icon = weather_icons.get(desc, weather_icons.get('정보없음'))
        
        # Resize Icon based on scale
        if w_icon:
            # Resize Icon based on font size (e.g. 1.2x font height)
            icon_sz = int(base_font_size * 1.5 * scale)
            w_icon = w_icon.resize((icon_sz, icon_sz), Image.Resampling.LANCZOS)

        lines.append(f"{weather_data['temp']:.1f}°C ({desc})")

        if weather_data.get('rain_forecast'):
            rf = weather_data['rain_forecast']
            rtype = ["", "비", "비/눈", "눈", "소나기"][rf['type_code']]
            lines.append(f"└ {rtype} {rf['start_time']}~ {rf['amount']:.1f}mm")
        elif weather_data.get('current_rain_amount', 0) > 0:
            lines.append(f"└ 현재 강수량: {weather_data['current_rain_amount']:.1f}mm")
    else:
        lines.append("날씨 정보 없음")
        w_icon = weather_icons.get('정보없음')
        if w_icon:
             icon_sz = int(base_font_size * 1.5 * scale)
             w_icon = w_icon.resize((icon_sz, icon_sz), Image.Resampling.LANCZOS)

    # 2. Dust Line
    dust_color = (128, 128, 128)
    if dust_data:
        grade, sym, color = get_dust_grade_info(dust_data.get('pm10'), dust_data.get('pm25'))
        # Line 1: Grade symbol & text
        lines.append(f"{sym} {grade}")
        # Line 2: Details
        lines.append(f"미세먼지 {dust_data['pm10']} | 초미세먼지 {dust_data['pm25']}")
        dust_color = color
    else:
        lines.append("미세먼지 정보 없음")

    # Time & Location Line
    time_str = datetime.now().strftime('%m/%d %H시 기준')
    if location_name:
         # Clean up location name (e.g., "Gyeonggi-do Pyeongtaek-si Godeok-myeon" -> "Godeok-myeon")
         short_loc = location_name.split()[-1]
         lines.append(f"{time_str} | {short_loc}")
    else:
         lines.append(time_str)

    # Dimensions
    line_spacing = int(5 * scale)
    line_heights = [font_lg.getmetrics()[0] + font_lg.getmetrics()[1] for _ in lines]
    
    # Calculate Max Width
    max_w = 0
    font_list = [font_lg] + [font_dt if i == len(lines)-2 else font_md for i in range(len(lines)-1)]
    
    # We need to simulate the layout to get box size
    total_h = 0
    for i, line in enumerate(lines):
        f = font_list[i]
        length = draw.textlength(line, f)
        if i == 0 and w_icon:
            length += w_icon.width + 5
        max_w = max(max_w, length)
        # Height accumulation
        total_h += f.getbbox("Tg")[3] + line_spacing 

    box_w = max_w + int(20 * scale)
    box_h = total_h + int(20 * scale)
    margin = int(15 * scale)

    # Position Calculation
    pos_x = layout_config.get('x')
    pos_y = layout_config.get('y')

    if pos_x is not None and pos_y is not None:
        try:
            box_x = int(float(pos_x))
            box_y = int(float(pos_y))
            # Boundary check
            box_x = max(0, min(box_x, DISPLAY_WIDTH - box_w))
            box_y = max(0, min(box_y, DISPLAY_HEIGHT - box_h))
        except:
            box_x = DISPLAY_WIDTH - box_w - margin
            box_y = margin
    else:
        pos = layout_config.get('position', 'top')
        box_x = DISPLAY_WIDTH - box_w - margin
        if pos == 'bottom':
            box_y = DISPLAY_HEIGHT - box_h - margin
        else:
            box_y = margin

    # Draw Box
    bg_alpha = int(255 * opacity)
    draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=int(12*scale), fill=(255, 255, 255, bg_alpha),
                           outline=(200, 200, 200), width=1)

    # Draw Text
    cy = box_y + int(10 * scale)
    cx = box_x + int(10 * scale)

    # Line 1: Weather
    if w_icon:
        # Center icon vertically relative to text
        # icon_y = cy + (line_heights[0] - w_icon.height) // 2 
        # For simple alignment, use cy
        overlay.paste(w_icon, (int(cx), int(cy)), w_icon)
        cx += w_icon.width + 5
    draw.text((cx, cy), lines[0], font=font_lg, fill=(0, 0, 0))
    
    # Use proper spacing for next line
    cy += font_lg.getbbox("Tg")[3] + line_spacing
    cx = box_x + int(10 * scale)

    # Remaining Lines
    for i, line in enumerate(lines[1:]):
        # Determine font logic matching calculation
        # Calculation logic: font_list = [font_lg] + ...
        # lines[1] is index 1 in lines, so font_list[1]
        
        # font_list logic recap:
        # font_list = [font_lg] + [font_dt if j == len(lines)-2 else font_md for j in range(len(lines)-1)]
        # For i in enumerate(lines[1:]): i starts at 0.
        # This corresponds to lines[i+1].
        # Font index is i+1.
        
        # Simple Logic:
        # if this is the last line: font_dt
        # else: font_md
        
        is_last = (i == len(lines) - 2) # lines[1:] has length len-1. if i == (len-1)-1... wait.
        # len(lines) = 5. lines[1:] len = 4. range 0,1,2,3.
        # Last index is 3.
        # Condition should be: if this is the actual last line.
        
        f = font_dt if i == len(lines) - 2 else font_md
        
        if "●" in line:
            sym, txt = line.split(' ', 1)
            draw.text((cx, cy), sym, font=f, fill=dust_color)
            draw.text((cx + draw.textlength(sym, f) + 5, cy), txt, font=f, fill=(0, 0, 0))
        else:
            draw.text((cx, cy), line, font=f, fill=(0, 0, 0))
            
        cy += f.getbbox("Tg")[3] + line_spacing

    final_image = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    return final_image, box_x, box_y, box_w, box_h
