import unittest
import numpy as np
import cv2
from app.detector.ela import perform_ela
from app.detector.fft import perform_fft
from app.detector.landmarks import detect_faces
from app.detector.engine import process_image

class TestDeepShieldForensics(unittest.TestCase):
    def setUp(self):
        # Create a dummy test image (solid background with a rectangle)
        self.test_img = np.zeros((300, 300, 3), dtype=np.uint8)
        cv2.rectangle(self.test_img, (50, 50), (250, 250), (120, 255, 120), -1)
        
    def test_ela_detector(self):
        """Verify that ELA executes and returns correct types/values."""
        ela_img, metrics = perform_ela(self.test_img, quality=90, scale=15)
        self.assertIsInstance(ela_img, np.ndarray)
        self.assertEqual(ela_img.shape, self.test_img.shape)
        self.assertIn("score", metrics)
        self.assertIn("variance", metrics)
        self.assertIsInstance(metrics["score"], float)

    def test_fft_detector(self):
        """Verify that FFT executes and returns correct frequency spectrum analysis."""
        # FFT requires square input, testing with resized face slice mock
        mock_face = cv2.resize(self.test_img, (128, 128))
        fft_img, metrics = perform_fft(mock_face)
        self.assertIsInstance(fft_img, np.ndarray)
        self.assertEqual(fft_img.shape, (128, 128, 3))
        self.assertIn("score", metrics)
        self.assertIn("radial_profile", metrics)
        self.assertIsInstance(metrics["radial_profile"], list)

    def test_face_detector_no_faces(self):
        """Verify that face detector handles images with no faces safely."""
        faces = detect_faces(self.test_img)
        self.assertIsInstance(faces, list)
        self.assertEqual(len(faces), 0)  # Rectangles aren't faces

    def test_engine_pipeline(self):
        """Verify that the engine processes raw image bytes successfully."""
        # Encode test image to jpeg bytes
        _, buffer = cv2.imencode('.jpg', self.test_img)
        img_bytes = buffer.tobytes()
        
        result = process_image(img_bytes)
        self.assertTrue(result["success"])
        self.assertEqual(result["face_count"], 0)
        self.assertIn("overall_score", result)
        self.assertIn("verdict", result)
        self.assertIn("ela_b64", result)
        self.assertIn("fft_b64", result)

if __name__ == "__main__":
    unittest.main()
