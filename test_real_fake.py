import urllib.request
from app.detector.engine import process_image

def test_url(url, label):
    print(f"Testing {label} image from {url}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            img_bytes = response.read()
        
        result = process_image(img_bytes)
        print(f"[{label.upper()}] Overall Score: {result.get('overall_score')}%")
        print(f"[{label.upper()}] Verdict: {result.get('verdict')}")
        print(f"[{label.upper()}] Faces Detected: {result.get('face_count')}")
        if result.get('face_count') > 0:
            for i, face in enumerate(result.get('faces', [])):
                print(f"  Face {i+1} Threat: {face.get('composite_score')}%")
                print(f"    FFT Score: {face.get('fft_score')}%")
                print(f"    ELA Score: {face.get('ela_score')}%")
                print(f"    Geom Score: {face.get('geometry_score')}%")
        print("-" * 50)
    except Exception as e:
        print(f"Error testing {label} image: {e}")

real_url = "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?ixlib=rb-4.0.3&w=400"
test_url(real_url, "Real")
