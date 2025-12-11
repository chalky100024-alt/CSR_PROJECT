import os
import time
import requests
from PIL import Image
import io
import logging
import settings
from huggingface_hub import InferenceClient # Official Library

logger = logging.getLogger(__name__)

# --- Models ---
TEXT2IMG_MODEL = "black-forest-labs/FLUX.1-schnell" # Best Free T2I
IMG2IMG_MODEL = "timbrooks/instruct-pix2pix"       # Best I2I Instruction

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
    
    # 1. Google Provider
    if provider == "google":
        api_key = config.get('api_key_google', config.get('api_key_ai'))
        if not api_key:
            logger.error(f"API Key for {provider} missing")
            return None
            
        full_prompt = f"{prompt}, {style_preset} style, HD, high quality"
        try:
            return _gen_google_vertex(full_prompt, api_key)
        except Exception as e:
            logger.error(f"Google Gen Failed: {e}")
            return None

    # 2. Hugging Face (Official Client)
    elif provider == "huggingface":
        client = _get_hf_client()
        if not client: return None

        # Auto-Translate
        try:
            from deep_translator import GoogleTranslator
            prompt = GoogleTranslator(source='auto', target='en').translate(prompt)
        except: pass

        if style_preset == "anime style": style_preset = "Studio Ghibli"

        full_prompt = f"{prompt}, {style_preset} style, high quality, 8k"
        logger.info(f"🎨 HF Request: {full_prompt}")

        try:
            image = client.text_to_image(prompt=full_prompt, model=TEXT2IMG_MODEL)
            return _save_result(image, "hf")
        except Exception as e:
            logger.error(f"❌ HF Failed: {e}")
            return None
    
    else:
        logger.error(f"Unknown provider: {provider}")
        return None


def generate_image_from_image(prompt, style_preset, source_path, provider="huggingface"):
    # Img2Img is HF ONLY for now
    if provider != "huggingface":
        logger.error("Img2Img only supported on Hugging Face")
        return None

    client = _get_hf_client()
    if not client: return None

    # Auto-Translate
    try:
        from deep_translator import GoogleTranslator
        if prompt: prompt = GoogleTranslator(source='auto', target='en').translate(prompt)
    except: pass

    if style_preset == "anime style": style_preset = "Studio Ghibli"
    
    # Load Source Image
    try:
        original_image = Image.open(source_path).convert("RGB")
    except Exception as e:
        logger.error(f"Invalid Source Image: {e}")
        return None

    # Instruct Pix2Pix Prompt
    instruction = f"Make it into {style_preset} style. {prompt}"
    logger.info(f"🎨 Img2Img Request: {instruction}")

    try:
        edited_image = client.image_to_image(
            image=original_image,
            prompt=instruction,
            model=IMG2IMG_MODEL,
            strength=0.8,
            guidance_scale=7.5,
            num_inference_steps=25
        )
        return _save_result(edited_image, "hf_edit")
    except Exception as e:
        logger.error(f"❌ Img2Img Failed: {e}")
        return None

# --- Helper Functions ---

def _gen_google_vertex(prompt, api_key):
    # Google Vertex AI (Rest API)
    config = settings.load_config()
    project_id = config.get('google_project_id')
    location = config.get('google_location', 'us-central1')
    
    if not project_id: return None

    model_id = "imagen-3.0-generate-001"
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:predict"
    
    headers = { "Content-Type": "application/json" }
    params = {"key": api_key}
    
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": { "sampleCount": 1, "aspectRatio": "16:9" }
    }
    
    response = requests.post(url, headers=headers, params=params, json=payload, timeout=60)
    
    if response.status_code != 200:
        logger.error(f"Google Error: {response.text}")
        return None
        
    try:
        res_json = response.json()
        b64_img = res_json['predictions'][0]['bytesBase64Encoded']
        img = Image.open(io.BytesIO(base64.b64decode(b64_img)))
        return _save_result(img, "google")
    except Exception as e:
        logger.error(f"Google Parse Error: {e}")
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
