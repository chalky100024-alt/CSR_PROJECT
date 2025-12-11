
import requests
import json

API_KEY = "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"
API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

def test_hf_gen():
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {"inputs": "A beautiful landscape of mountains and river, digital art"}
    
    print(f"Testing URL: {API_URL}")
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        
        try:
            print(f"Response Text: {response.json()}")
        except:
            print(f"Response Content (First 200 bytes): {response.content[:200]}")
            
    except Exception as e:
        print(f"Request Error: {e}")

if __name__ == "__main__":
    test_hf_gen()
