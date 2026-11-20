"""
DeepShield — Test Image Generator
===================================
Generates synthetic test images specifically designed to trigger
each of the 3 detection signals in the DeepShield forensic pipeline:

  1. REAL  — Clean authentic-looking image (baseline, should score low)
  2. ELA   — Compression mismatch (face pasted from different JPEG save)
  3. FFT   — Checkerboard/grid artifact (GAN-style periodic noise)
  4. GEOM  — Mirrored face (perfect horizontal symmetry, MAE < 4)
  5. FULL  — All 3 signals combined (should score ~80-100%)

Run: python generate_test_images.py
Output: test_images/ folder
"""

import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import os


def make_base_face(width=400, height=400, bg_color=(110, 85, 60)):
    """Creates a simple synthetic portrait with a face oval and features."""
    img = np.full((height, width, 3), bg_color, dtype=np.uint8)
    cx, cy = width // 2, height // 2

    # Face oval (skin tone)
    cv2.ellipse(img, (cx, cy), (110, 140), 0, 0, 360, (210, 175, 140), -1)

    # Eyes
    cv2.ellipse(img, (cx - 38, cy - 30), (22, 12), 0, 0, 360, (255, 255, 255), -1)
    cv2.ellipse(img, (cx + 38, cy - 30), (22, 12), 0, 0, 360, (255, 255, 255), -1)
    cv2.circle(img,  (cx - 38, cy - 30), 9, (60, 40, 20), -1)
    cv2.circle(img,  (cx + 38, cy - 30), 9, (60, 40, 20), -1)
    cv2.circle(img,  (cx - 35, cy - 33), 3, (255, 255, 255), -1)
    cv2.circle(img,  (cx + 41, cy - 33), 3, (255, 255, 255), -1)

    # Eyebrows
    cv2.ellipse(img, (cx - 38, cy - 52), (25, 7), -10, 0, 180, (60, 35, 15), -1)
    cv2.ellipse(img, (cx + 38, cy - 52), (25, 7),  10, 0, 180, (60, 35, 15), -1)

    # Nose
    pts_nose = np.array([[cx, cy - 5], [cx - 12, cy + 25], [cx + 12, cy + 25]], np.int32)
    cv2.polylines(img, [pts_nose], True, (180, 130, 100), 2)

    # Mouth
    cv2.ellipse(img, (cx, cy + 55), (30, 12), 0, 0, 180, (160, 80, 80), -1)
    cv2.ellipse(img, (cx, cy + 48), (30, 8), 0, 0, 180, (210, 175, 140), -1)

    # Hair
    cv2.ellipse(img, (cx, cy - 85), (115, 80), 0, 180, 360, (50, 30, 10), -1)

    # Neck
    cv2.rectangle(img, (cx - 30, cy + 135), (cx + 30, height), (210, 175, 140), -1)

    # Shoulders
    cv2.ellipse(img, (cx, height - 20), (160, 60), 0, 180, 360, (80, 60, 90), -1)

    return img


def jpeg_round_trip(img_bgr, quality=85):
    """Saves an image to JPEG in memory at 'quality' and reloads it."""
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    buf = BytesIO()
    pil.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    reloaded = np.array(Image.open(buf))
    return cv2.cvtColor(reloaded, cv2.COLOR_RGB2BGR)


# ─────────────────────────────────────────────────────────────
# 1. AUTHENTIC BASELINE
# ─────────────────────────────────────────────────────────────
def make_authentic_baseline(output_path):
    print("  [1/5] Generating: Authentic Baseline...")
    base = make_base_face(400, 400, bg_color=(100, 90, 75))

    # Natural texture noise
    noise = np.random.normal(0, 4, base.shape).astype(np.int16)
    noisy = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Slight asymmetric shadow (natural lighting)
    result = noisy.copy().astype(np.float32)
    result[:, :180] *= 0.92  # left-side shadow
    result = np.clip(result, 0, 255).astype(np.uint8)

    # Single consistent JPEG compression (no mixed history)
    cv2.imwrite(output_path, result, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"    Saved -> {output_path}")
    print("    Expected Score: LOW  | Verdict: ORIGINAL (AUTHENTIC)")


# ─────────────────────────────────────────────────────────────
# 2. ELA TRIGGER — Compression History Mismatch
# ─────────────────────────────────────────────────────────────
def make_ela_trigger(output_path):
    print("  [2/5] Generating: ELA Trigger (compression mismatch)...")
    base = make_base_face(400, 400, bg_color=(90, 110, 80))

    # Save background at high quality (minimal JPEG compression)
    background = jpeg_round_trip(base, quality=95)

    # Take the face region and apply HEAVY compression separately
    # This simulates a face sourced from a different file/save
    face_region = base[60:340, 90:310].copy()
    face_heavy = jpeg_round_trip(face_region, quality=18)

    # Paste the differently-compressed face back onto the clean background
    manipulated = background.copy()
    manipulated[60:340, 90:310] = face_heavy

    cv2.imwrite(output_path, manipulated, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"    Saved -> {output_path}")
    print("    Expected Score: ELA HIGH | face/bg compression ratio >> 2.0")


# ─────────────────────────────────────────────────────────────
# 3. FFT TRIGGER — Checkerboard Periodic Artifact (GAN-style)
# ─────────────────────────────────────────────────────────────
def make_fft_trigger(output_path):
    print("  [3/5] Generating: FFT Trigger (checkerboard artifact)...")
    base = make_base_face(400, 400, bg_color=(70, 80, 100))
    result = base.copy().astype(np.float32)

    # 4-pixel tile checkerboard = simulates GAN transposed conv stride artifact
    tile = 4
    h, w = result.shape[:2]
    for y in range(h):
        for x in range(w):
            if (x // tile + y // tile) % 2 == 0:
                result[y, x] += 22

    # Restrict noise to face oval only
    mask = np.zeros((h, w), dtype=np.float32)
    cv2.ellipse(mask, (200, 200), (110, 140), 0, 0, 360, 1.0, -1)
    mask_3ch = np.stack([mask] * 3, axis=-1)

    final = (result * mask_3ch + base.astype(np.float32) * (1 - mask_3ch))
    final = np.clip(final, 0, 255).astype(np.uint8)

    cv2.imwrite(output_path, final, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"    Saved -> {output_path}")
    print("    Expected Score: FFT HIGH | peak_ratio >> 9.0 in high-frequency band")


# ─────────────────────────────────────────────────────────────
# 4. GEOMETRY TRIGGER — Mirror-Perfect Face (MAE < 4)
# ─────────────────────────────────────────────────────────────
def make_geometry_trigger(output_path):
    print("  [4/5] Generating: Geometry Trigger (mirror-perfect symmetry)...")
    base = make_base_face(400, 400)

    # Mirror the left half exactly onto the right half
    mid = 200
    left_half = base[:, :mid].copy()
    base[:, mid:] = cv2.flip(left_half, 1)

    # Very subtle seam blur (as a real deepfake blending tool would do)
    base[:, mid-3:mid+3] = cv2.GaussianBlur(base[:, mid-3:mid+3], (5, 5), 2)

    cv2.imwrite(output_path, base, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"    Saved -> {output_path}")
    print("    Expected Score: GEOMETRY HIGH | is_mirror_fake=True, MAE < 4.0")


# ─────────────────────────────────────────────────────────────
# 5. FULL DEEPFAKE — All 3 Signals Combined
# ─────────────────────────────────────────────────────────────
def make_full_deepfake(output_path):
    print("  [5/5] Generating: FULL Deepfake (all 3 signals combined)...")
    base = make_base_face(400, 400, bg_color=(60, 70, 90))

    # SIGNAL 1 — Mirror (Geometry)
    mid = 200
    left_half = base[:, :mid].copy()
    base[:, mid:] = cv2.flip(left_half, 1)

    # SIGNAL 2 — Checkerboard noise (FFT)
    tile = 4
    h, w = base.shape[:2]
    noise_layer = base.copy().astype(np.float32)
    for y in range(h):
        for x in range(w):
            if (x // tile + y // tile) % 2 == 0:
                noise_layer[y, x] += 20

    face_mask = np.zeros((h, w), dtype=np.float32)
    cv2.ellipse(face_mask, (200, 200), (110, 140), 0, 0, 360, 1.0, -1)
    face_mask_3ch = np.stack([face_mask] * 3, axis=-1)

    with_noise = (noise_layer * face_mask_3ch + base.astype(np.float32) * (1 - face_mask_3ch))
    with_noise = np.clip(with_noise, 0, 255).astype(np.uint8)

    # SIGNAL 3 — Compression mismatch (ELA)
    background = jpeg_round_trip(with_noise, quality=95)
    face_region = with_noise[60:340, 90:310].copy()
    face_heavy = jpeg_round_trip(face_region, quality=16)
    background[60:340, 90:310] = face_heavy

    cv2.imwrite(output_path, background, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"    Saved -> {output_path}")
    print("    Expected Score: ~80-100% | Verdict: MANIPULATED (DEEPFAKE)")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_images")
    os.makedirs(out_dir, exist_ok=True)

    print("\n" + "=" * 60)
    print("        DeepShield — Test Image Generator")
    print("=" * 60)
    print(f"\nOutput folder: {out_dir}\n")

    make_authentic_baseline(os.path.join(out_dir, "1_authentic_baseline.jpg"))
    print()
    make_ela_trigger(os.path.join(out_dir, "2_ela_trigger.jpg"))
    print()
    make_fft_trigger(os.path.join(out_dir, "3_fft_trigger.jpg"))
    print()
    make_geometry_trigger(os.path.join(out_dir, "4_geometry_mirror.jpg"))
    print()
    make_full_deepfake(os.path.join(out_dir, "5_full_deepfake.jpg"))

    print("\n" + "=" * 60)
    print("All 5 test images generated successfully!")
    print("=" * 60)
    print("""
Upload Guide — test each in DeepShield at http://localhost:8000

  1_authentic_baseline.jpg  ->  LOW score   (Authentic)
  2_ela_trigger.jpg         ->  ELA spikes  (compression mismatch)
  3_fft_trigger.jpg         ->  FFT spikes  (checkerboard artifact)
  4_geometry_mirror.jpg     ->  GEOM spikes (mirror face)
  5_full_deepfake.jpg       ->  ALL HIGH    (DEEPFAKE verdict)

Watch the terminal logs for per-signal diagnostic breakdown!
""")
