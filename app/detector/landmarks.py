import cv2
import numpy as np

# Load the face cascade classifier from OpenCV's built-in data
face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(face_cascade_path)

# Load eye cascade for additional verification if needed
eye_cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

def detect_faces(image_bgr: np.ndarray) -> list[dict]:
    """
    Detects faces in an image using Haar Cascade Classifier.
    
    Args:
        image_bgr: BGR format image.
        
    Returns:
        List of face dictionaries, containing 'box' (x, y, w, h) and other metadata.
    """
    try:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        # Equalize histogram to improve detection under varying light
        gray_eq = cv2.equalizeHist(gray)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray_eq,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        face_list = []
        for (x, y, w, h) in faces:
            # Crop face region
            face_roi = image_bgr[y:y+h, x:x+w]
            
            # Analyze symmetry & blending
            symmetry_score, details = analyze_face_geometry(face_roi)
            
            face_list.append({
                "box": [int(x), int(y), int(w), int(h)],
                "geometry_score": symmetry_score,
                "geometry_details": details
            })
            
        return face_list
    except Exception as e:
        print(f"Error detecting faces: {e}")
        return []

def analyze_face_geometry(face_roi: np.ndarray) -> tuple[float, dict]:
    """
    Analyzes the structural and pixel symmetry of a cropped face,
    and checks for blending boundaries.
    
    Args:
        face_roi: Cropped BGR face region.
        
    Returns:
        A tuple of (geometry_deepfake_score, details)
    """
    try:
        h, w, c = face_roi.shape
        if h < 20 or w < 20:
            return 0.0, {"error": "Face ROI too small"}
            
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        
        # --- 1. Structural Symmetry ---
        # Find the vertical centerline
        mid = w // 2
        
        # Divide into left and right halves
        left_half = gray[:, :mid]
        right_half = gray[:, mid:2*mid]
        
        # Ensure they are equal size
        min_w = min(left_half.shape[1], right_half.shape[1])
        left_half = left_half[:, :min_w]
        right_half = right_half[:, :min_w]
        
        # Flip the right half horizontally to match the left half orientation
        right_flipped = cv2.flip(right_half, 1)
        
        # Resize both to standard size to compare
        std_size = (64, 128)
        left_res = cv2.resize(left_half, std_size)
        right_res = cv2.resize(right_flipped, std_size)
        
        # Calculate Absolute Difference between left and right sides
        sym_diff = cv2.absdiff(left_res, right_res)
        sym_mae = float(np.mean(sym_diff))  # Mean Absolute Error
        
        # Normalize MAE to a scale. High MAE = low symmetry (asymmetrical features, typical in poor fakes)
        # Or a highly artificial symmetry (exact mirror, MAE close to 0) which is also unnatural.
        # Natural faces have MAE in range of 12 - 65 due to natural shadows and pose.
        is_mirror = sym_mae < 4.0
        is_highly_asymmetric = sym_mae > 75.0
        
        # --- 2. Blending Boundary Checks ---
        # Deepfakes often have artificial smoothing at the seam where the face is blended into the background.
        # We calculate the image gradient (Laplacian/Sobel) along the border of the face box vs. the interior.
        # Face interior should be high-detail, borders should not be excessively blurred compared to interior.
        
        # Interior region (central 70% area)
        int_y1, int_y2 = int(h * 0.15), int(h * 0.85)
        int_x1, int_x2 = int(w * 0.15), int(w * 0.85)
        interior = gray[int_y1:int_y2, int_x1:int_x2]
        
        # Borders (horizontal and vertical margins)
        border_top = gray[0:int_y1, :]
        border_bottom = gray[int_y2:h, :]
        border_left = gray[int_y1:int_y2, 0:int_x1]
        border_right = gray[int_y1:int_y2, int_x2:w]
        
        # Combine borders into a list of pixel values
        border_pixels = np.concatenate([
            border_top.flatten(),
            border_bottom.flatten(),
            border_left.flatten(),
            border_right.flatten()
        ])
        
        # Compute Laplace variance (blurriness metric)
        interior_blur = cv2.Laplacian(interior, cv2.CV_64F).var()
        if len(border_pixels) > 0:
            # Reconstruct borders as one continuous matrix to run Laplacian on it
            border_h = len(border_pixels) // 64
            if border_h > 2:
                border_mat = border_pixels[:border_h * 64].reshape((border_h, 64))
                border_blur = cv2.Laplacian(border_mat, cv2.CV_64F).var()
            else:
                border_blur = interior_blur  # Default if border cannot be calculated
        else:
            border_blur = interior_blur
            
        # Compare blur: deepfakes often blur boundaries to hide transitions,
        # leading to border_blur being way smaller than interior_blur.
        blur_ratio = float(border_blur / (interior_blur + 1e-9))
        
        # Compute geometry threat score (0 to 100)
        score = 0.0
        if is_mirror:
            score += 40.0  # Excessive matching (copy-paste face)
        elif is_highly_asymmetric:
            score += 50.0  # Asymmetric anomalies
        else:
            # Score scaling between nominal symmetry limits
            # Natural symmetry MAE is up to 65.
            if sym_mae > 65.0:
                score += min(40.0, (sym_mae - 65.0) * 3.0)
                
        # Blending border penalty
        # Only flag if face interior is sharp (detail > 100) and border is extremely soft (blur_ratio < 0.08)
        if interior_blur > 100.0 and blur_ratio < 0.08:
            score += min(40.0, (0.08 - blur_ratio) * 500.0)
            
        score = min(100.0, score)
        
        details = {
            "symmetry_mae": sym_mae,
            "blur_ratio": blur_ratio,
            "interior_detail": float(interior_blur),
            "border_detail": float(border_blur),
            "is_mirror_fake": bool(is_mirror),
            "is_asymmetric_fake": bool(is_highly_asymmetric)
        }
        
        return score, details
    except Exception as e:
        return 0.0, {"error": str(e)}
