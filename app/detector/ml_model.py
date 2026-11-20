import numpy as np
import os

# ---------------------------------------------------------------------------
# ML Model — currently DISABLED due to hardware constraints.
# The HuggingFace ViT model (umm-maybe/AI-image-detector) runs at ~350 MB
# and produces high false-positive rates on real photographs.
# To re-enable: set ML_MODEL_ENABLED = True and ensure sufficient hardware.
# ---------------------------------------------------------------------------

ML_MODEL_ENABLED = False

_ml_pipeline = None

def get_ml_pipeline():
    global _ml_pipeline
    if not ML_MODEL_ENABLED:
        return None
    if _ml_pipeline is None:
        try:
            print("[INFO] Loading Deepfake Detection ML Model... This may take a moment.")
            from transformers import pipeline
            _ml_pipeline = pipeline("image-classification", model="umm-maybe/AI-image-detector")
            print("[INFO] ML Model loaded successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to load ML Model: {e}")
            return None
    return _ml_pipeline

def predict_deepfake_ml(image_bgr: np.ndarray) -> dict:
    """
    Predicts whether an image is AI-generated using a pretrained Vision Transformer.

    Currently DISABLED. Returns a neutral stub so the engine falls back to
    pure heuristic (ELA + FFT + Geometry) scoring.

    Args:
        image_bgr: BGR image (unused when disabled).

    Returns:
        dict with:
            - 'ml_score': 0.0 (neutral — does not bias the composite score)
            - 'label': 'Disabled'
            - 'success': False
    """
    pipe = get_ml_pipeline()
    if not pipe:
        # Return a neutral stub so the engine can still run heuristics only
        return {"success": False, "ml_score": 0.0, "label": "Disabled"}

    try:
        import cv2
        from PIL import Image

        rgb_image = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)

        results = pipe(pil_image)

        fake_score = 0.0
        real_score = 0.0

        for res in results:
            label = res['label'].lower()
            score = res['score'] * 100.0

            if any(k in label for k in ['fake', 'spoof', 'manipulated', 'artificial', 'ai']):
                fake_score = max(fake_score, score)
            elif any(k in label for k in ['real', 'authentic', 'original', 'human']):
                real_score = max(real_score, score)

        if fake_score == 0.0 and real_score > 0.0:
            fake_score = 100.0 - real_score
        elif real_score == 0.0 and fake_score > 0.0:
            real_score = 100.0 - fake_score

        final_score = fake_score

        return {
            "success": True,
            "ml_score": float(final_score),
            "label": "Fake" if final_score >= 50.0 else "Real"
        }
    except Exception as e:
        print(f"[ERROR] ML inference failed: {e}")
        return {"success": False, "ml_score": 0.0, "label": "Error"}
