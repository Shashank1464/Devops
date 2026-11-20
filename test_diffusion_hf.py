import cv2
import numpy as np
from PIL import Image
import urllib.request
import json
import os

# Load environment variables from .env file if it exists
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip("'\"")

urls = {
    'REAL1': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?ixlib=rb-4.0.3&w=400',
    'FAKE_GAN': 'https://thispersondoesnotexist.com',
    'FAKE_DALLE': 'https://upload.wikimedia.org/wikipedia/commons/4/4d/DALL-E_3_generated_image_of_a_cyberpunk_city.jpg'
}

def test_model(model_name):
    print(f"\n--- Testing Model: {model_name} ---")
    try:
        from transformers import pipeline
        pipe = pipeline("image-classification", model=model_name)
        
        for label, url in urls.items():
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            img_bytes = urllib.request.urlopen(req).read()
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            
            res = pipe(pil_img)
            print(f"[{label}] -> {res}")
    except Exception as e:
        print(f"Error testing {model_name}: {e}")

test_model("capcheck/ai-image-detection")
test_model("umm-maybe/AI-image-detector")
