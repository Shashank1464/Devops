import urllib.request
import cv2
import numpy as np
from app.detector.engine import process_image

real_url = 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?ixlib=rb-4.0.3&w=400'
dalle_url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/DALL-E_3_generated_image_of_a_cyberpunk_city.jpg/400px-DALL-E_3_generated_image_of_a_cyberpunk_city.jpg'
gan_url = 'https://thispersondoesnotexist.com'

def test(url, label):
    try:
        print(f"Testing {label}...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        img_bytes = urllib.request.urlopen(req).read()
        res = process_image(img_bytes)
        print(f"[{label}] Overall Score: {res.get('overall_score', 0):.2f}% -> Verdict: {res.get('verdict')}")
        if res.get('face_count', 0) > 0:
            face = res['faces'][0]
            print(f"  ML Score: {face.get('ml_score', 0):.2f}%")
            print(f"  FFT: {face.get('fft_score', 0):.2f}% | ELA: {face.get('ela_score', 0):.2f}% | Geom: {face.get('geometry_score', 0):.2f}%")
    except Exception as e:
        print(f"[{label}] Error: {e}")

test(real_url, 'REAL')
test(gan_url, 'GAN')
test(dalle_url, 'DALL-E')
