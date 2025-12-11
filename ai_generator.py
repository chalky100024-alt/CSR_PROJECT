import os
import time
import requests
from PIL import Image
import io
import logging
import settings

logger = logging.getLogger(__name__)

# Hugging Face 무료 모델 (FLUX.1-schnell 추천)
HF_API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

def generate_image(prompt, style_preset, provider="huggingface"):
    config = settings.load_config()
    api_key = config.get('api_key_ai')
    
    if not api_key:
        logger.error("AI API Key가 없습니다.")
        return None

    # Auto-Translate to English if needed
    try:
        from deep_translator import GoogleTranslator
        # Use 'auto' source
        translated = GoogleTranslator(source='auto', target='en').translate(prompt)
        logger.info(f"Translated Prompt: {prompt} -> {translated}")
        prompt = translated
    except ImportError:
        logger.warning("deep-translator not installed, skipping translation")
    except Exception as e:
        logger.error(f"Translation failed: {e}")

    # Style mapping reform
    if style_preset == "anime style":
        style_preset = "Studio Ghibli"
    
    # Subject first, then style.
    full_prompt = f"{prompt}. {style_preset} style, HD, high quality"
    logger.info(f"Generating with Prompt: [{full_prompt}]")
    
    try:
        if provider == "huggingface":
            return _gen_huggingface(full_prompt, api_key)
        elif provider == "openai":
            return _gen_dalle3(full_prompt, api_key)
        elif provider == "google":
            return _gen_google_vertex(full_prompt, api_key)
    except Exception as e:
        logger.error(f"AI 생성 실패: {e}")
        return None

def _gen_huggingface(prompt, api_key):
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"inputs": prompt}
    
    logger.info(f"HuggingFace 요청 중...: {prompt}")
    response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
    
    if response.status_code != 200:
        logger.error(f"HF Error: {response.text}")
        return None
        
    image_bytes = response.content
    img = Image.open(io.BytesIO(image_bytes))
    return _save_result(img, "hf")

def _gen_dalle3(prompt, api_key):
    # DALL-E 3는 `openai` 라이브러리 필요하지만 requests로 구현 가능
    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024"
    }
    
    logger.info("DALL-E 3 요청 중...")
    res = requests.post(url, headers=headers, json=data, timeout=60)
    if res.status_code != 200:
        logger.error(f"OpenAI Error: {res.text}")
        return None
        
    img_url = res.json()['data'][0]['url']
    img_data = requests.get(img_url).content
    img = Image.open(io.BytesIO(img_data))
    return _save_result(img, "dalle")

def _gen_google_vertex(prompt, api_key):
    # Google Vertex AI (Imagen 3) via REST API with API Key
    # URL: https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/{LOCATION}/publishers/google/models/{MODEL}:predict?key={KEY}
    
    config = settings.load_config()
    project_id = config.get('google_project_id')
    location = config.get('google_location', 'us-central1')
    
    if not project_id:
        logger.error("Google Project ID is missing")
        return None

    # Model: imagen-3.0-generate-001 (or similar)
    model_id = "image-generation-001" # Standard Imagen 2/3 endpoint often uses this generic tag or specific version
    # Let's try the specific one user might expect    # Model: Use "imagen-3.0-generate-001" as requested by user
    model_id = "imagen-3.0-generate-001"

    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:predict"
    
    headers = {
        "Content-Type": "application/json"
    }
    # Important: When using API Key, it is passed as query param, NOT header
    params = {"key": api_key}
    
    payload = {
        "instances": [
            {"prompt": prompt}
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "16:9" 
        }
    }
    
    # Add aspect ratio parameter correct format
    payload["parameters"]["aspectRatio"] = "16:9" 
    
    logger.info(f"Google Vertex Request: {prompt}")
    response = requests.post(url, headers=headers, params=params, json=payload, timeout=60)
    
    if response.status_code != 200:
        logger.error(f"Google Vertex Error: {response.text}")
        return None
        
    try:
        # Vertex Response: { "predictions": [ "base64_string_..." ] }
        res_json = response.json()
        b64_img = res_json['predictions'][0]['bytesBase64Encoded']
        
        img_data = base64.b64decode(b64_img)
        img = Image.open(io.BytesIO(img_data))
        return _save_result(img, "google")
    except Exception as e:
        logger.error(f"Google Parse Failed: {e}")
        return None

def _save_result(img, prefix):
    # Resize to 800x480 (Fill/Crop)
    target_w, target_h = 800, 480
    
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h
    
    if img_ratio > target_ratio:
        # Image is wider -> scale by height
        new_h = target_h
        new_w = int(img.width * (target_h / img.height))
    else:
        # Image is taller/square -> scale by width
        new_w = target_w
        new_h = int(img.height * (target_w / img.width))
        
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Center Crop
    left = (new_w - target_w) / 2
    top = (new_h - target_h) / 2
    img = img.crop((left, top, left + target_w, top + target_h))

    filename = f"ai_{prefix}_{int(time.time())}.png"
    save_path = os.path.join(settings.UPLOADS_DIR, filename)
    img.save(save_path)
    logger.info(f"이미지 저장됨: {save_path}")
    return filename

# --- Image to Image ---
import base64

# Use INSTRUCT-PIX2PIX for real image editing
IMG2IMG_URL = "https://router.huggingface.co/hf-inference/models/timbrooks/instruct-pix2pix"

def generate_image_from_image(prompt, style_preset, source_path, provider="huggingface"):
    config = settings.load_config()
    api_key = config.get('api_key_ai')
    
    if not api_key: return None
    
    # Simple Translation
    try:
        from deep_translator import GoogleTranslator
        if prompt and len(prompt) > 1:
            prompt = GoogleTranslator(source='auto', target='en').translate(prompt)
    except: pass
    
    # Clean style preset logic
    if style_preset == "anime style":
        style_preset = "Studio Ghibli"
        
    style_text = style_preset
    if "style" in style_preset.lower() and "style" in prompt.lower():
         style_text = style_preset.replace("style", "").replace("Style", "").strip()

    # Instruct Pix2Pix Prompt
    full_prompt = f"make it into {style_preset} style, {prompt}"
    
    try:
        if provider == "huggingface":
            return _gen_hf_img2img(full_prompt, source_path, api_key)
        else:
            # Fallback to normal gen for others (Img2Img not supported for Dalle/Google yet in this code)
            return generate_image(prompt, style_preset, provider)
    except Exception as e:
        logger.error(f"Img2Img Failed: {e}")
        return None

def _gen_hf_img2img(prompt, source_path, api_key):
    # Instruct-Pix2Pix Payload
    with open(source_path, "rb") as f:
        img_bytes = f.read()
    
    b64_img = base64.b64encode(img_bytes).decode('utf-8')
    
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "image": b64_img,
            "num_inference_steps": 25,
            "image_guidance_scale": 1.5,
            "guidance_scale": 7.5
        }
    }
    
    logger.info(f"HF Img2Img Request: {prompt}")
    response = requests.post(IMG2IMG_URL, headers=headers, json=payload, timeout=60)
    
    if response.status_code != 200:
        logger.error(f"HF Img2Img Error: {response.text}")
        return None
        
    image_bytes = response.content
    try:
        img = Image.open(io.BytesIO(image_bytes))
        return _save_result(img, "hf_edit")
    except:
        logger.error(f"Response not image: {response.text}")
        return None
