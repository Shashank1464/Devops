import cv2
import numpy as np
import base64

def perform_fft(face_image_bgr: np.ndarray, size: int = 128) -> tuple[np.ndarray, dict]:
    """
    Performs a 2D Fast Fourier Transform on a face image to detect periodic artifacts.
    
    Args:
        face_image_bgr: BGR face crop image.
        size: Size to resize the face to (standardized grid size).
        
    Returns:
        A tuple of (fft_spectrum_bgr, metrics)
        - fft_spectrum_bgr: Visual 2D FFT magnitude spectrum (grayscale visualized in BGR).
        - metrics: Dictionary of frequency domain metrics (high_frequency_power, peak_anomalies, score).
    """
    try:
        # Resize to fixed square dimension
        resized = cv2.resize(face_image_bgr, (size, size))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        
        # Convert to float and perform 2D FFT
        dft = np.fft.fft2(gray.astype(np.float32))
        dft_shift = np.fft.fftshift(dft)
        
        # Calculate magnitude spectrum (log scale for human visualization)
        magnitude = np.abs(dft_shift)
        log_mag = 20 * np.log(magnitude + 1e-9)
        
        # Normalize to 0-255 for visualization
        min_val, max_val = log_mag.min(), log_mag.max()
        if max_val > min_val:
            normalized_mag = ((log_mag - min_val) / (max_val - min_val) * 255).astype(np.uint8)
        else:
            normalized_mag = np.zeros_like(log_mag, dtype=np.uint8)
            
        # Create a colormap visual for the UI (e.g., INFERNO or JET) to make it look premium
        fft_visual = cv2.applyColorMap(normalized_mag, cv2.COLORMAP_INFERNO)
        
        # Forensic Calculations
        # 1. Split magnitude spectrum into frequency bands (low, mid, high)
        # We can do this by measuring distance from the center (size//2, size//2)
        cx, cy = size // 2, size // 2
        y, x = np.ogrid[-cx:size-cx, -cy:size-cy]
        r = np.sqrt(x*x + y*y)
        
        # Define mask filters for bands
        r_max = size * np.sqrt(2) / 2
        low_mask = r < (r_max * 0.2)
        mid_mask = (r >= (r_max * 0.2)) & (r < (r_max * 0.6))
        high_mask = r >= (r_max * 0.6)
        
        # Compute mean power in each band
        low_power = float(np.mean(magnitude[low_mask]))
        mid_power = float(np.mean(magnitude[mid_mask]))
        high_power = float(np.mean(magnitude[high_mask]))
        
        # Calculate ratio of high-to-mid power. 
        # Natural faces decay rapidly, so high_power is extremely small compared to low/mid power.
        # GANs/Diffusions generate high frequency grid peaks, increasing high-frequency power.
        power_ratio = high_power / (mid_power + 1e-9)
        
        # 2. Check for sharp periodic peaks in the high frequency band (checkerboard artifacts)
        # We look at standard deviation and max-to-mean ratio in high frequencies.
        high_freq_vals = magnitude[high_mask]
        max_high = np.max(high_freq_vals) if len(high_freq_vals) > 0 else 0
        mean_high = np.mean(high_freq_vals) if len(high_freq_vals) > 0 else 1
        std_high = np.std(high_freq_vals) if len(high_freq_vals) > 0 else 0
        
        peak_ratio = float(max_high / (mean_high + 1e-9))
        variance_ratio = float(std_high / (mean_high + 1e-9))
        
        # Compute deepfake score based on peak anomalies (Crest Factor).
        # Crest Factor (peak_ratio): max value in high freqs divided by mean value.
        # Real JPEG-compressed faces have smooth high-freq decay but can reach peak_ratio
        # of 7–20 purely due to DCT block artifacts — so the threshold must sit above that noise floor.
        # GAN/Diffusion checkerboard patterns produce highly structured peaks, reliably above 10.0+.
        # Threshold 9.0 sits safely above the JPEG noise floor while still catching synthetic artifacts.
        # Scaling is gentler (15.0 vs. previous 25.0) to avoid dramatic jumps near the boundary.
        peak_score = min(100.0, max(0.0, (peak_ratio - 9.0) * 15.0))
        
        # Composite FFT deepfake score relies purely on the peak frequency anomaly
        score = peak_score
        score = min(100.0, max(0.0, score))
        
        # Generate radial profile coordinates for charting in the UI (1D Graph)
        # We calculate the average magnitude at each pixel radius
        r_int = r.astype(int)
        radial_profile = []
        max_radius = int(r_max)
        for i in range(0, max_radius):
            radial_val = magnitude[r_int == i]
            if len(radial_val) > 0:
                radial_profile.append(float(np.mean(radial_val)))
            else:
                radial_profile.append(0.0)
                
        # Normalize radial profile for clean plotting
        max_profile = max(radial_profile) if len(radial_profile) > 0 else 1.0
        radial_profile_normalized = [val / max_profile for val in radial_profile]
        
        metrics = {
            "low_power": low_power,
            "mid_power": mid_power,
            "high_power": high_power,
            "power_ratio": power_ratio,
            "peak_ratio": peak_ratio,
            "variance_ratio": variance_ratio,
            "score": score,
            "radial_profile": radial_profile_normalized[:35]  # Keep first 35 data points for frontend chart
        }
        
        return fft_visual, metrics
    except Exception as e:
        return np.zeros((size, size, 3), dtype=np.uint8), {
            "low_power": 0.0, "mid_power": 0.0, "high_power": 0.0,
            "power_ratio": 0.0, "peak_ratio": 0.0, "variance_ratio": 0.0,
            "score": 0.0, "radial_profile": [], "error": str(e)
        }

def get_base64_fft(fft_image: np.ndarray) -> str:
    """Converts the FFT visual spectrum image NumPy array into a base64 JPEG string."""
    _, buffer = cv2.imencode('.jpg', fft_image)
    b64_str = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{b64_str}"
