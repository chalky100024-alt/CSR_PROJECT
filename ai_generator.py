import os
import time
import requests
from PIL import Image
import io
import base64
import logging
import settings
from huggingface_hub import InferenceClient # Official Library

try:
    from utils.logger import log_debug
except ImportError:
    log_debug = lambda msg, level='info': None

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
    # User Request: Timeout 30s
    return InferenceClient(token=api_key, timeout=30)

def generate_image(prompt, style_preset, provider="huggingface", image_filenames=None):
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
            image_paths = []
            if image_filenames:
                 # Check if it's a list (new method) or single string (legacy safe)
                if isinstance(image_filenames, list):
                    image_paths = [os.path.join(settings.UPLOADS_DIR, f) for f in image_filenames]
                else:
                    image_paths = [os.path.join(settings.UPLOADS_DIR, image_filenames)]
                
            return _gen_gemini_flash(full_prompt, api_key, image_paths)
        except Exception as e:
            logger.error(f"Google Gen Failed: {e}")
            return None

    # 2. Hugging Face (Official Client)
    elif provider == "huggingface":
        client = _get_hf_client()
        if not client: return None

        try:
            log_debug(f"AI Gen Start: HuggingFace ({TEXT2IMG_MODEL})")
            t0 = time.time()
            image = client.text_to_image(prompt=full_prompt, model=TEXT2IMG_MODEL)
            dt = time.time() - t0
            log_debug(f"AI Gen Success: {dt:.2f}s")
            return _save_result(image, "hf")
        except Exception as e:
            logger.error(f"❌ HF Failed: {e}")
            return None
    
    else:
        logger.error(f"Unknown provider: {provider}")
        return None




# --- Helper Functions ---

def _get_token_from_service_account():
    """FETCH ACCESS TOKEN VIA SERVICE ACCOUNT JSON (Robust for Pi/Server)"""
    try:
        import google.auth
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request as GoogleAuthRequest

        config = settings.load_config()
        sa_json_str = config.get('api_key_google') # In settings, this field holds the JSON string
        
        if not sa_json_str or "private_key" not in sa_json_str:
            # Fallback to gcloud if no JSON provided (local dev)
            return _get_gcloud_token()
            
        # Parse JSON
        import json
        sa_info = json.loads(sa_json_str)
        
        # Create Credentials
        creds = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # Refresh Token
        creds.refresh(GoogleAuthRequest())
        return creds.token, sa_info.get('project_id')

    except ImportError:
        logger.error("❌ 'google-auth' library missing. Run: pip install google-auth requests")
        return _get_gcloud_token() # Fallback
    except Exception as e:
        logger.error(f"Service Account Auth Failed: {e}")
        return None, None

def _get_gcloud_token():
    """Fallback: FETCH ACCESS TOKEN VIA GCLOUD CLI"""
    import subprocess
    try:
        token = subprocess.check_output("gcloud auth print-access-token", shell=True).decode('utf-8').strip()
        project_id = settings.load_config().get('google_project_id')
        if not project_id:
            project_id = subprocess.check_output("gcloud config get-value project", shell=True).decode('utf-8').strip()
        return token, project_id
    except:
        return None, None

def _gen_gemini_flash(prompt, _unused_api_key, image_paths=None):
    # Strict Usage: Vertex AI (OAuth2)
    # Model: gemini-2.5-flash-image (Nano Banana)
    
    token, project_id = _get_token_from_service_account()
    
    if not token or not project_id:
        logger.error("❌ Auth Failed. Please set Service Account JSON in Settings or run gcloud login.")
        return None

    location = "us-central1"
    model_id = "gemini-2.5-flash-image"
    
    # Vertex AI Endpoint
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:generateContent"
    
    headers = { 
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}" # OAuth2 Token
    }
    
    # Payload: Same as AI Studio
    # Construct Parts
    parts = [{"text": prompt}]
    
    # Add Images if provided
    if image_paths:
        for img_path in image_paths:
            if os.path.exists(img_path):
                try:
                    with open(img_path, "rb") as image_file:
                        image_data = base64.b64encode(image_file.read()).decode('utf-8')
                        
                    parts.append({
                        "inlineData": {
                            "mimeType": "image/jpeg", # Assuming JPEG for now
                            "data": image_data
                        }
                    })
                    logger.info(f"📸 Attached Image: {os.path.basename(img_path)}")
                except Exception as e:
                    logger.error(f"Failed to read image {img_path}: {e}")
    
    payload = {
        "contents": [{
            "role": "user",
            "parts": parts
        }]
    }
    
    logger.info(f"⚡️ Calling Vertex AI ({model_id})...")
    logger.debug(f"URL: {url}")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            res_json = response.json()
            candidates = res_json.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                for part in parts:
                    # Check for inline data (Image)
                    if 'inlineData' in part:
                        b64_img = part['inlineData']['data']
                        img = Image.open(io.BytesIO(base64.b64decode(b64_img)))
                        return _save_result(img, "gemini_vertex")
                    # Check for text (if model refused to generate image)
                    if 'text' in part:
                         logger.warning(f"Gemini returned Text instead of Image: {part['text']}")
            
            logger.error(f"Generate success but no image data: {res_json}")
            return None
            
        else:
            logger.error(f"Vertex AI Failed: {response.status_code}")
            logger.error(f"Response Body: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Vertex AI Exception: {e}")
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
