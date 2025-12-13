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
    # Fallback to Imagen 3.0 (Stable) as Gemini 2.5 Flash seems to have Auth issues with API Keys
    model_id = "imagen-3.0-generate-001" 
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:predict"
    
    # Imagen requires different payload usually (instances) but let's check if it supports generateContent via AI Studio
    # AI Studio 'generateContent' works for newer models.
    # If using 'imagen-3.0-generate-001', it might be via 'predict' endpoint on Vertex, but for AI Studio:
    # Let's try 'gemini-1.5-flash' which is definitely open.
    # BUT Gemini 1.5 Flash is NOT an image generator.
    
    # Let's try the exact Nano Banana setup from the notebook again, maybe it was v1beta
    model_id = "gemini-2.5-flash-image"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"
    
    headers = { "Content-Type": "application/json" }
    params = {"key": api_key}
    
    # Payload Refinement: Maybe 'response_modalities' caused the 401/400?
    # Or maybe the model is just 'gemini-2.0-flash-exp'? 
    # Let's try without generationConfig first (default)
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    logger.info(f"⚡️ Calling Gemini Flash ({model_id})...")
    response = requests.post(url, headers=headers, params=params, json=payload, timeout=60)
    
    if response.status_code != 200:
        logger.error(f"Gemini Error: {response.text}")
        return None
        
    try:
        res_json = response.json()
        # Parse Gemini Response: candidates[0].content.parts[0].inlineData.data
        # Note: Sometimes text is returned if image gen fails or is filtered, but usually inlineData
        candidates = res_json.get('candidates', [])
        if not candidates:
            logger.error("No candidates in response")
            return None
            
        parts = candidates[0].get('content', {}).get('parts', [])
        for part in parts:
            if 'inlineData' in part:
                b64_img = part['inlineData']['data']
                img = Image.open(io.BytesIO(base64.b64decode(b64_img)))
                return _save_result(img, "gemini")
                
        logger.error("No image data found in response parts")
        return None

    except Exception as e:
        logger.error(f"Gemini Parse Error: {e}")
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
