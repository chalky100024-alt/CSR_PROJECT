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
    "api_key_hf": "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", # User's HF Key (Hardcoded request)
    "ai_provider": "huggingface", # or 'openai'
    "ai_provider": "huggingface", # or 'openai'
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

    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # Default Key Injection (Fallback)
            if 'api_key_kma' not in config:
                config['api_key_kma'] = "F3I3IeSUH4yLzn6o45Qwob4eGGydLmGax83sAzxr3FH2h82xRoHO5afglEMsRuQ6enj4qJaF2UCQo89cSWHyKg=="
                config['api_key_air'] = "F3I3IeSUH4yLzn6o45Qwob4eGGydLmGax83sAzxr3FH2h82xRoHO5afglEMsRuQ6enj4qJaF2UCQo89cSWHyKg=="
            return config
    except:
        return DEFAULT_CONFIG

def save_config(config_data):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)

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
