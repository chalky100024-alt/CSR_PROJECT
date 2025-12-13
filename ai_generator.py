import os
import time
import requests
from PIL import Image
import io
import base64
import logging
import settings
from huggingface_hub import InferenceClient # Official Library

logger = logging.getLogger(__name__)

# --- Models ---
TEXT2IMG_MODEL = "black-forest-labs/FLUX.1-schnell" # Best Free T2I


def _get_hf_client():
    config = settings.load_config()
    api_key = config.get('api_key_hf') # Use proper HF key
    if not api_key: api_key = config.get('api_key_ai') # Fallback
    
    if not api_key:
        logger.error("❌ HF API Key가 없습니다.")
        return None
    return InferenceClient(token=api_key)

def generate_image(prompt, style_preset, provider="huggingface"):
    config = settings.load_config()
    
    # 0. Common Pre-processing (Translation & Style Mapping)
    # 0. Common Pre-processing (Translation & Style Mapping)
    # Auto-Translate (Korean -> English) - Only for HuggingFace
    if provider == "huggingface":
        try:
            from deep_translator import GoogleTranslator
            if prompt and any(ord(c) > 127 for c in prompt): # Simple check if translation needed
                translated = GoogleTranslator(source='auto', target='en').translate(prompt)
                logger.info(f"🔤 Translate (HF): {prompt} -> {translated}")
                prompt = translated
        except Exception as e:
            logger.warning(f"Translation failed: {e}")

    # Style Mapping
    if style_preset == "anime style": 
        style_preset = "Studio Ghibli"
    elif style_preset == "lego":
        style_preset = "Lego Brick"
    
    # Clean up double 'style' if present in preset
    clean_style = style_preset.replace(" style", "")
    
    # Common Prompt Construction
    if style_preset == "no_style":
        full_prompt = f"{prompt}, HD, high quality, 8k"
    else:
        full_prompt = f"{prompt}, {clean_style} style, HD, high quality, 8k"
        
    logger.info(f"🎨 Generate Request ({provider}): {full_prompt}")

    # 1. Google Provider
    if provider == "google":
        api_key = config.get('api_key_google', config.get('api_key_ai'))
        if not api_key:
            logger.error(f"API Key for {provider} missing")
            return None
            
        try:
            return _gen_gemini_flash(full_prompt, api_key)
        except Exception as e:
            logger.error(f"Google Gen Failed: {e}")
            return None

    # 2. Hugging Face (Official Client)
    elif provider == "huggingface":
        client = _get_hf_client()
        if not client: return None

        try:
            image = client.text_to_image(prompt=full_prompt, model=TEXT2IMG_MODEL)
            return _save_result(image, "hf")
        except Exception as e:
            logger.error(f"❌ HF Failed: {e}")
            return None
    
    else:
        logger.error(f"Unknown provider: {provider}")
        return None




# --- Helper Functions ---

def _gen_gemini_flash(prompt, api_key):
    # Attempt 1: Nano Banana (Gemini 2.5 Flash Image) - User Preference
    # Ref: User mentioned using Vertex Key. If 401, we try standard headers.
    models_to_try = [
        "gemini-2.5-flash-image", 
        "gemini-2.0-flash-exp" # Fallback to latest experimental flash
    ]
    
    for model_id in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"
        
        # Headers: Explicitly include x-goog-api-key for robustness (some proxies/vertex-like behaviors require it)
        headers = { 
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        params = {"key": api_key}
        
        # Payload: Standard text-to-image prompt
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            # We explicitly ask for IMAGE via modalities if supported, 
            # but for 2.5/2.0 it might be implicit or via tools.
            # Start simple to minimize 400 Bad Request
        }
        
        logger.info(f"⚡️ Calling {model_id}...")
        try:
            response = requests.post(url, headers=headers, params=params, json=payload, timeout=60)
            
            if response.status_code == 200:
                res_json = response.json()
                candidates = res_json.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    for part in parts:
                        if 'inlineData' in part:
                            b64_img = part['inlineData']['data']
                            img = Image.open(io.BytesIO(base64.b64decode(b64_img)))
                            return _save_result(img, "gemini_flash")
                
                logger.warning(f"{model_id} worked but no image data found: {res_json}")
                # Continue config/prompt refinement if needed
                
            else:
                logger.warning(f"{model_id} failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"{model_id} Exception: {e}")
            
    # If all fail, return None (User explicitly rejected Imagen 3.0 fallback)
    logger.error("❌ All Gemini Flash attempts failed. Recommend checking API Key permissions for 'Generative Language API'.")
    return None

def _gen_dalle3(prompt, api_key):
    # DALL-E 3 (Optional Legacy)
    return None 

def _save_result(img, prefix):
    # Resize to 800x480 (Fill/Crop)
    target_w, target_h = 800, 480
    
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h
    
    if img_ratio > target_ratio:
        new_h = target_h
        new_w = int(img.width * (target_h / img.height))
    else:
        new_w = target_w
        new_h = int(img.height * (target_w / img.width))
        
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    left = (new_w - target_w) / 2
    top = (new_h - target_h) / 2
    img = img.crop((left, top, left + target_w, top + target_h))

    filename = f"ai_{prefix}_{int(time.time())}.png"
    save_path = os.path.join(settings.UPLOADS_DIR, filename)
    img.save(save_path)
    logger.info(f"✅ Saved: {save_path}")
    return filename
