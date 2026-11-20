import cv2
import numpy as np
from io import BytesIO
from PIL import Image
import base64

def perform_ela(image_np: np.ndarray, face_boxes: list = None, quality: int = 90, scale: int = 15) -> tuple[np.ndarray, dict]:
    """
    Performs Error Level Analysis (ELA) on a NumPy image (BGR format).
    
    Args:
        image_np: Image matrix in BGR format.
        face_boxes: Optional list of detected face bounding boxes.
        quality: JPEG compression quality (0-100) to resave the image at.
        scale: Amplification factor for the difference.
        
    Returns:
        A tuple of (ela_image_bgr, metrics)
    """
    try:
        # Convert BGR (OpenCV) to RGB (PIL)
        rgb_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_image)
        
        # Save to memory buffer as JPEG with specified quality
        buffer = BytesIO()
        pil_img.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)
        
        # Reload the compressed image
        compressed_pil = Image.open(buffer)
        compressed_np = np.array(compressed_pil)
        
        # Convert back to BGR for calculations and return format consistency
        compressed_bgr = cv2.cvtColor(compressed_np, cv2.COLOR_RGB2BGR)
        
        # Calculate absolute difference
        abs_diff = cv2.absdiff(image_np, compressed_bgr)
        
        # Amplify the difference to make inconsistencies visible
        ela_image = abs_diff * scale
        ela_image = np.clip(ela_image, 0, 255).astype(np.uint8)
        
        # Calculate statistics on the ELA map
        # Convert to grayscale for statistical analysis
        gray_ela = cv2.cvtColor(ela_image, cv2.COLOR_BGR2GRAY)
        h, w = gray_ela.shape
        
        mean_diff = float(np.mean(gray_ela))
        var_diff = float(np.var(gray_ela))
        max_diff = float(np.max(gray_ela))
        
        # --- Localized Reference-Based Scoring ---
        fake_score = 10.0 # Default base noise floor for real compressed images
        
        if face_boxes and len(face_boxes) > 0:
            # Compare face ELA variance against the background ELA variance.
            # Crop the first face
            fx, fy, fw, fh = face_boxes[0]
            # Keep within bounds
            fx1, fy1 = max(0, fx), max(0, fy)
            fx2, fy2 = min(w, fx+fw), min(h, fy+fh)
            
            face_crop = gray_ela[fy1:fy2, fx1:fx2]
            if face_crop.size > 0:
                face_var = np.var(face_crop)
                
                # Background mask (excluding the face box)
                bg_mask = np.ones_like(gray_ela, dtype=bool)
                bg_mask[fy1:fy2, fx1:fx2] = False
                bg_pixels = gray_ela[bg_mask]
                
                bg_var = np.var(bg_pixels) if bg_pixels.size > 0 else var_diff
                
                # Compare ratio
                var_ratio = face_var / (bg_var + 1e-9)
                
                # Deepfakes show localized variance disparity because the face has a different compression history.
                # A ratio far from 1.0 (e.g. < 0.5 or > 2.0) indicates manipulation.
                # Natural faces have higher texture variance than their background, so we allow up to 1.0 deviation
                # (i.e., var_ratio anywhere from 0.5 to 2.0) before raising the score above the noise floor.
                if var_ratio > 1.0:
                    deviation = var_ratio - 1.0
                else:
                    deviation = (1.0 / (var_ratio + 1e-9)) - 1.0

                if deviation > 1.0:
                    fake_score = min(100.0, 10.0 + (deviation - 1.0) * 45.0)
                else:
                    # Within natural variation — keep close to baseline
                    fake_score = max(5.0, 5.0 + deviation * 8.0)
        else:
            # No face boxes. Check grid variance dispersion (global copy-paste detector).
            # Divide into 4x4 blocks
            rows, cols = 4, 4
            block_h, block_w = h // rows, w // cols
            block_variances = []
            
            for r in range(rows):
                for c in range(cols):
                    block = gray_ela[r*block_h:(r+1)*block_h, c*block_w:(c+1)*block_w]
                    if block.size > 0:
                        block_variances.append(np.var(block))
            
            if len(block_variances) > 1:
                # Calculate dispersion (standard deviation of the local variances normalized by their mean)
                mean_block_var = np.mean(block_variances)
                std_block_var = np.std(block_variances)
                dispersion = std_block_var / (mean_block_var + 1e-9)
                
                # Normal images have uniform compression dispersion (< 0.8)
                # Spliced images have a localized spike, driving up dispersion
                if dispersion > 0.7:
                    fake_score = min(100.0, 10.0 + (dispersion - 0.7) * 50.0)
                else:
                    fake_score = max(5.0, 5.0 + dispersion * 10.0)
                    
        # Flat image anomaly check
        if mean_diff < 0.2:
            fake_score = 5.0  # Perfect lossless image or pure black mock
            
        metrics = {
            "mean_difference": mean_diff,
            "variance": var_diff,
            "max_difference": max_diff,
            "score": float(fake_score)
        }
        
        return ela_image, metrics
    except Exception as e:
        # Graceful error handling
        return np.zeros_like(image_np), {"mean_difference": 0.0, "variance": 0.0, "max_difference": 0.0, "score": 0.0, "error": str(e)}

def get_base64_ela(ela_image: np.ndarray) -> str:
    """Converts the ELA image NumPy array into a base64 JPEG string for web transmission."""
    _, buffer = cv2.imencode('.jpg', ela_image)
    b64_str = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{b64_str}"
