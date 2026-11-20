import cv2
import numpy as np
import os
import time
from .ela import perform_ela, get_base64_ela
from .fft import perform_fft, get_base64_fft
from .landmarks import detect_faces, analyze_face_geometry
from .ml_model import predict_deepfake_ml

def process_image(image_bytes: bytes) -> dict:
    """
    Processes an image through the ELA, FFT, and face geometry detectors.
    
    Args:
        image_bytes: Raw bytes of the uploaded image.
        
    Returns:
        Dictionary of analysis results.
    """
    # Decode image from bytes
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return {"success": False, "error": "Invalid image format or corrupted file"}
        
    h, w, c = img.shape
    
    # 1. Detect faces
    faces = detect_faces(img)
    face_boxes = [f["box"] for f in faces] if faces else None
    
    # 2. Run global ELA on the full image (with face reference context)
    ela_img, ela_metrics = perform_ela(img, face_boxes=face_boxes, quality=90, scale=15)
    ela_b64 = get_base64_ela(ela_img)
    
    face_details = []
    fft_b64 = None
    radial_profile = []
    
    if len(faces) > 0:
        # We found faces. Let's analyze each face crop.
        for face in faces:
            x, y, fw, fh = face["box"]
            
            # Ensure crop stays within image bounds
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(w, x+fw), min(h, y+fh)
            face_roi = img[y1:y2, x1:x2]
            
            if face_roi.size == 0:
                continue
                
            # Run FFT on face crop
            fft_img, fft_metrics = perform_fft(face_roi)
            
            # Use the first face's FFT image to display in the primary visualizer
            if fft_b64 is None:
                fft_b64 = get_base64_fft(fft_img)
                radial_profile = fft_metrics["radial_profile"]
                
            # --- Heuristic-only composite scoring ---
            # ML model is currently disabled (hardware constraints).
            # Score is derived purely from ELA, FFT, and Geometry signals.
            ml_res = predict_deepfake_ml(img)  # Returns disabled stub: ml_score=0.0
            ml_score = 0.0  # Always 0 while disabled — does not bias composite

            face_ela_score = ela_metrics["score"]
            face_fft_score = fft_metrics["score"]
            face_geom_score = face["geometry_score"]

            # Weighted heuristic composite:
            # ELA (50%): most reliable for copy-paste/splice detection
            # FFT (30%): catches checkerboard GAN artifacts (threshold raised to reduce JPEG noise)
            # Geometry (20%): catches blending seams and severe asymmetry
            composite_score = (
                (face_ela_score * 0.50)
                + (face_fft_score * 0.30)
                + (face_geom_score * 0.20)
            )
            composite_score = min(100.0, max(0.0, composite_score))

            # Print diagnostic logs to the local terminal
            print(f"\n[FORENSIC DIAGNOSIS] Target face at {face['box']}:")
            print(f"  - ML Model:                Disabled (heuristic-only mode)")
            print(f"  - FFT Anomaly Score:       {face_fft_score:.2f}% (Peak ratio: {fft_metrics['peak_ratio']:.2f})")
            print(f"  - ELA Compression Score:   {face_ela_score:.2f}% (Face vs Background)")
            print(f"  - Geometry/Symmetry:       {face_geom_score:.2f}% (MAE symmetry error)")
            print(f"  - Composite Threat Index:  {composite_score:.2f}%")

            face_details.append({
                "box": face["box"],
                "fft_score": face_fft_score,
                "ela_score": face_ela_score,
                "geometry_score": face_geom_score,
                "composite_score": composite_score,
                "ml_score": ml_score,
                "ml_label": ml_res["label"],
                "geometry_details": face["geometry_details"],
                "fft_details": {
                    "power_ratio": fft_metrics["power_ratio"],
                    "peak_ratio": fft_metrics["peak_ratio"]
                }
            })

        # Overall page score is the max of detected face threat scores.
        # Verdict threshold raised to 65% to reduce false positives on real photographs.
        overall_score = max([f["composite_score"] for f in face_details])
        verdict = "MANIPULATED (DEEPFAKE)" if overall_score >= 65.0 else "ORIGINAL (AUTHENTIC)"
    else:
        # No faces detected. Set default safe score
        print("\n[FORENSIC DIAGNOSIS] No faces detected in the image. Defaulting to safe baseline.")
        overall_score = 12.0
        verdict = "AUTHENTIC (NO FACE DETECTED)"
        
    return {
        "success": True,
        "filename": "Uploaded Photo",
        "resolution": f"{w}x{h}",
        "face_count": len(faces),
        "overall_score": overall_score,
        "verdict": verdict,
        "ela_metrics": ela_metrics,
        "ela_b64": ela_b64,
        "fft_b64": fft_b64,
        "radial_profile": radial_profile,
        "faces": face_details
    }

def process_video(video_path: str, max_frames: int = 15) -> dict:
    """
    Processes a video file, extracting frames and checking for temporal consistency.
    
    Args:
        video_path: Filepath to the video.
        max_frames: Max frames to analyze (to control execution time).
        
    Returns:
        Dictionary of video analysis results.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"success": False, "error": "Could not open video file"}
        
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    duration = total_frames / fps
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Calculate step size to sample 'max_frames' evenly across video
    step = max(1, total_frames // max_frames)
    
    frames_analyzed = 0
    timeline = []
    face_boxes_history = []
    
    # Visualizers for the frontend (we'll capture the worst-scoring frame to show as summary)
    worst_frame_score = -1.0
    worst_ela_b64 = None
    worst_fft_b64 = None
    worst_radial_profile = []
    worst_frame_boxes = []
    
    for frame_idx in range(0, total_frames, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break
            
        timestamp = frame_idx / fps
        
        # Perform face detection first
        faces = detect_faces(frame)
        face_boxes = [f["box"] for f in faces] if faces else None
        
        # Perform image analysis on this frame (with face reference context)
        _, ela_metrics = perform_ela(frame, face_boxes=face_boxes, quality=90, scale=15)
        
        frame_score = 0.0
        frame_faces = []
        
        if len(faces) > 0:
            for face in faces:
                x, y, fw, fh = face["box"]
                x1, y1 = max(0, x), max(0, y)
                x2, y2 = min(width, x+fw), min(height, y+fh)
                face_roi = frame[y1:y2, x1:x2]
                
                if face_roi.size > 0:
                    fft_img, fft_metrics = perform_fft(face_roi)
                    # Match the image scoring weights: ELA 50%, FFT 30%, Geometry 20%
                    face_score = (ela_metrics["score"] * 0.50) + (fft_metrics["score"] * 0.30) + (face["geometry_score"] * 0.20)
                    
                    frame_faces.append({
                        "box": face["box"],
                        "score": face_score
                    })
                    
                    # Capture visual outputs for the worst frame to display as report highlights
                    if face_score > worst_frame_score:
                        worst_frame_score = face_score
                        # Encode worst visuals
                        ela_img, _ = perform_ela(frame, quality=90, scale=15)
                        worst_ela_b64 = get_base64_ela(ela_img)
                        worst_fft_b64 = get_base64_fft(fft_img)
                        worst_radial_profile = fft_metrics["radial_profile"]
                        worst_frame_boxes = [f["box"] for f in faces]
            
            # Frame score is max face score
            frame_score = max([f["score"] for f in frame_faces])
            face_boxes_history.append([f["box"] for f in frame_faces])
        else:
            # No face detected in this frame. Default to safe baseline noise score.
            frame_score = 10.0
            face_boxes_history.append([])
            
        timeline.append({
            "frame_index": frame_idx,
            "timestamp": round(timestamp, 2),
            "score": frame_score,
            "face_count": len(frame_faces)
        })
        
        frames_analyzed += 1
        if frames_analyzed >= max_frames:
            break
            
    cap.release()
    
    # --- Temporal Consistency Analysis ---
    # We calculate the standard deviation and variance of the facial positions and scores.
    # Rapid frame-to-frame score shifts or sudden jumps in face coordinates point to stitching issues.
    scores = [f["score"] for f in timeline]
    avg_score = float(np.mean(scores)) if scores else 0.0
    max_score = float(np.max(scores)) if scores else 0.0
    std_score = float(np.std(scores)) if scores else 0.0
    
    # Frame-to-frame jitter (first difference)
    jitter = 0.0
    if len(scores) > 1:
        diffs = np.abs(np.diff(scores))
        jitter = float(np.mean(diffs))
        
    # Temporal anomaly score penalty
    # Natural videos have stable compression and features (low standard deviation & jitter).
    # Deepfakes feature sudden frame jitters (high variance).
    temporal_penalty = min(30.0, (jitter / 8.0) * 30.0)
    
    overall_video_score = (avg_score * 0.7) + (max_score * 0.2) + temporal_penalty
    overall_video_score = min(100.0, max(0.0, overall_video_score))
    
    # Verdict threshold raised to 65% to match image analysis and reduce false positives.
    verdict = "MANIPULATED (DEEPFAKE)" if overall_video_score >= 65.0 else "ORIGINAL (AUTHENTIC)"
    
    # If no worst visuals were captured (e.g. no faces found), capture from first frame
    if worst_ela_b64 is None and frames_analyzed > 0:
        # Fallback to general video details
        worst_frame_score = overall_video_score
        worst_radial_profile = []
        
    return {
        "success": True,
        "filename": os.path.basename(video_path),
        "duration_seconds": round(duration, 2),
        "resolution": f"{width}x{height}",
        "fps": round(fps, 2),
        "frames_analyzed": frames_analyzed,
        "overall_score": overall_video_score,
        "verdict": verdict,
        "timeline": timeline,
        "temporal_metrics": {
            "average_frame_score": avg_score,
            "max_frame_score": max_score,
            "score_std_dev": std_score,
            "temporal_jitter": jitter,
            "temporal_penalty": temporal_penalty
        },
        "worst_frame_visuals": {
            "score": worst_frame_score,
            "ela_b64": worst_ela_b64,
            "fft_b64": worst_fft_b64,
            "radial_profile": worst_radial_profile,
            "face_boxes": worst_frame_boxes
        }
    }
