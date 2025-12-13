import os
import json

# --- 경로 설정 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, 'my_frame_web')
CONFIG_PATH = os.path.join(WEB_DIR, 'config.json')
UPLOADS_DIR = os.path.join(WEB_DIR, 'uploads')
STATIC_DIR = os.path.join(WEB_DIR, 'static')
PREVIEW_PATH = os.path.join(STATIC_DIR, 'preview.jpg')
DB_PATH = os.path.join(BASE_DIR, 'korea_zone.db')

# --- 기본 설정값 ---
DEFAULT_CONFIG = {
    "api_key_kma": "",      # 기상청 키
    "api_key_air": "",      # 에어코리아 키
    "api_key_ai": "",       # Deprecated (Shared)
    "api_key_google": "",   # Google Vertex AI Key
    "api_key_hf": "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", # User's HF Key (Restored)
    "ai_provider": "huggingface", # or 'google'
    "layout": {
        "type": "type_A",
        "widget_size": 1.0, # 0.5 ~ 1.5
        "font_size": 20,
        "position": "top"   # top, bottom
    },
    "location": {
        "name": "경기도 평택시 고덕동",
        "nx": 61,
        "ny": 115
    },
    "station_name": "고덕" # 미세먼지 측정소
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        # Try to load template
        template_path = os.path.join(BASE_DIR, 'my_frame_web', 'config_template.json')
        if os.path.exists(template_path):
            try:
                import shutil
                shutil.copy(template_path, CONFIG_PATH)
            except:
                pass
        
        # If still no config, return default
        if not os.path.exists(CONFIG_PATH):
            return DEFAULT_CONFIG

    # Retry logic for reading to avoid race conditions
    import time
    for i in range(3):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Default Key Injection (Fallback)
                if 'api_key_kma' not in config:
                    config['api_key_kma'] = "F3I3IeSUH4yLzn6o45Qwob4eGGydLmGax83sAzxr3FH2h82xRoHO5afglEMsRuQ6enj4qJaF2UCQo89cSWHuKg=="
                    config['api_key_air'] = "F3I3IeSUH4yLzn6o45Qwob4eGGydLmGax83sAzxr3FH2h82xRoHO5afglEMsRuQ6enj4qJaF2UCQo89cSWHuKg=="
                return config
        except Exception as e:
            if i == 2: # Last attempt
                print(f"Error loading config: {e}")
                pass # Use default below
            time.sleep(0.1)
            
    # Return default with correct keys if load failed
    defaults = DEFAULT_CONFIG.copy()
    defaults['api_key_kma'] = "F3I3IeSUH4yLzn6o45Qwob4eGGydLmGax83sAzxr3FH2h82xRoHO5afglEMsRuQ6enj4qJaF2UCQo89cSWHuKg=="
    defaults['api_key_air'] = "F3I3IeSUH4yLzn6o45Qwob4eGGydLmGax83sAzxr3FH2h82xRoHO5afglEMsRuQ6enj4qJaF2UCQo89cSWHuKg=="
    return defaults

def save_config(config_data):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    # Atomic write: Write to temp file then rename
    tmp_path = CONFIG_PATH + '.tmp'
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, CONFIG_PATH)
    except Exception as e:
        print(f"Error saving config: {e}")
        if os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except: pass

def get_font_path(bold=True):
    # Apple산돌고딕 또는 나눔고딕 우선 사용
    fonts = [
        os.path.join(BASE_DIR, "Apple_산돌고딕_Neo", "AppleSDGothicNeoB.ttf"),
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    for f in fonts:
        if os.path.exists(f): return f
    return None
