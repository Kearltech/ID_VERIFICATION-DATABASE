"""
Enhanced face comparison module for passport photo and ID card image matching.

Provides multiple face detection and comparison methods:
1. OpenCV Haar Cascade (baseline, always available)
2. OpenCV DNN face detection (better accuracy)
3. Histogram-based comparison
4. Structural similarity (SSIM)
5. Feature-based matching (ORB, SIFT)
"""

import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Dict, Optional, List
import os

# Import optional libraries
try:
    from skimage.metrics import structural_similarity as ssim
    _have_skimage = True
except ImportError:
    _have_skimage = False

try:
    import imutils
    from imutils import face_utils
    _have_imutils = True
except ImportError:
    _have_imutils = False


class FaceComparator:
    """
    Advanced face comparison using multiple techniques.
    """
    
    def __init__(self):
        """Initialize face detection models."""
        # Load Haar Cascade (lightweight, always available)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Try to load DNN face detector (better accuracy)
        self.dnn_model = None
        try:
            model_path = cv2.data.haarcascades.replace('haarcascades', 'data')
            prototxt = os.path.join(model_path, 'deploy.prototxt')
            caffemodel = os.path.join(model_path, 'res10_300x300_ssd_iter_140000.caffemodel')
            
            # Alternative: try local paths or download
            if not os.path.exists(prototxt):
                # Model files not found, will use Haar Cascade only
                pass
            else:
                self.dnn_model = cv2.dnn.readNetFromCaffe(prototxt, caffemodel)
        except Exception:
            pass  # Fall back to Haar Cascade
    
    def detect_faces_haar(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces using Haar Cascade.
        
        Args:
            image: Input image as numpy array (BGR format)
            
        Returns:
            List of (x, y, w, h) tuples for detected faces
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        return [(x, y, w, h) for (x, y, w, h) in faces]
    
    def detect_faces_dnn(self, image: np.ndarray, confidence_threshold: float = 0.5) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces using DNN model (if available).
        
        Args:
            image: Input image as numpy array (BGR format)
            confidence_threshold: Minimum confidence for detection
            
        Returns:
            List of (x, y, w, h) tuples for detected faces
        """
        if self.dnn_model is None:
            return self.detect_faces_haar(image)
        
        (h, w) = image.shape[:2]
        blob = cv2.dnn.blobFromImage(
            cv2.resize(image, (300, 300)), 1.0,
            (300, 300), (104.0, 177.0, 123.0)
        )
        
        self.dnn_model.setInput(blob)
        detections = self.dnn_model.forward()
        
        faces = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > confidence_threshold:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                faces.append((startX, startY, endX - startX, endY - startY))
        
        return faces
    
    def compare_histogram(self, face1: np.ndarray, face2: np.ndarray) -> float:
        """
        Compare faces using histogram correlation.
        
        Args:
            face1, face2: Face images as numpy arrays
            
        Returns:
            Distance score (0-1, lower is more similar)
        """
        # Resize to same size
        face1 = cv2.resize(face1, (100, 100))
        face2 = cv2.resize(face2, (100, 100))
        
        # Compute histograms
        hist1 = cv2.calcHist([face1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist2 = cv2.calcHist([face2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        
        # Normalize
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()
        
        # Bhattacharyya distance (0 = identical, 1 = completely different)
        distance = cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)
        
        return distance
    
    def compare_ssim(self, face1: np.ndarray, face2: np.ndarray) -> float:
        """
        Compare faces using Structural Similarity Index (SSIM).
        
        Args:
            face1, face2: Face images as numpy arrays
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        if not _have_skimage:
            # Fallback to histogram comparison
            return 1.0 - self.compare_histogram(face1, face2)
        
        # Resize to same size
        face1 = cv2.resize(face1, (100, 100))
        face2 = cv2.resize(face2, (100, 100))
        
        # Convert to grayscale
        gray1 = cv2.cvtColor(face1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(face2, cv2.COLOR_BGR2GRAY)
        
        # Compute SSIM
        score = ssim(gray1, gray2)
        
        return score
    
    def compare_features(self, face1: np.ndarray, face2: np.ndarray) -> float:
        """
        Compare faces using ORB feature matching.
        
        Args:
            face1, face2: Face images as numpy arrays
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        # Resize to same size
        face1 = cv2.resize(face1, (200, 200))
        face2 = cv2.resize(face2, (200, 200))
        
        # Convert to grayscale
        gray1 = cv2.cvtColor(face1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(face2, cv2.COLOR_BGR2GRAY)
        
        # Initialize ORB detector
        orb = cv2.ORB_create(nfeatures=500)
        
        # Detect keypoints and descriptors
        kp1, des1 = orb.detectAndCompute(gray1, None)
        kp2, des2 = orb.detectAndCompute(gray2, None)
        
        if des1 is None or des2 is None or len(des1) < 2 or len(des2) < 2:
            return 0.0
        
        # Match descriptors using BFMatcher
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        
        # Sort matches by distance
        matches = sorted(matches, key=lambda x: x.distance)
        
        # Calculate similarity score
        if len(matches) == 0:
            return 0.0
        
        # Good matches are those with low distance
        good_matches = [m for m in matches if m.distance < 50]
        similarity = len(good_matches) / max(len(kp1), len(kp2))
        
        return min(similarity, 1.0)
    
    def compare_faces(
        self,
        pil_img1: Image.Image,
        pil_img2: Image.Image,
        method: str = 'ensemble'
    ) -> Tuple[bool, float, Dict[str, float]]:
        """
        Compare two face images using specified method(s).
        
        Args:
            pil_img1: First image (portrait)
            pil_img2: Second image (ID card)
            method: Comparison method - 'histogram', 'ssim', 'features', or 'ensemble'
            
        Returns:
            Tuple of (match_boolean, overall_score, method_scores_dict)
        """
        # Convert PIL to OpenCV format
        img1 = cv2.cvtColor(np.array(pil_img1), cv2.COLOR_RGB2BGR)
        img2 = cv2.cvtColor(np.array(pil_img2), cv2.COLOR_RGB2BGR)
        
        # Detect faces
        faces1 = self.detect_faces_dnn(img1)
        if len(faces1) == 0:
            faces1 = self.detect_faces_haar(img1)
        
        faces2 = self.detect_faces_dnn(img2)
        if len(faces2) == 0:
            faces2 = self.detect_faces_haar(img2)
        
        if len(faces1) == 0 or len(faces2) == 0:
            return None, None, {'error': 'No faces detected'}
        
        # Extract face regions
        x1, y1, w1, h1 = faces1[0]
        x2, y2, w2, h2 = faces2[0]
        
        face1 = img1[y1:y1+h1, x1:x1+w1]
        face2 = img2[y2:y2+h2, x2:x2+w2]
        
        # Compute similarity scores
        scores = {}
        
        if method in ['histogram', 'ensemble']:
            scores['histogram'] = 1.0 - self.compare_histogram(face1, face2)
        
        if method in ['ssim', 'ensemble'] and _have_skimage:
            scores['ssim'] = self.compare_ssim(face1, face2)
        
        if method in ['features', 'ensemble']:
            scores['features'] = self.compare_features(face1, face2)
        
        # Calculate overall score
        if method == 'ensemble':
            overall_score = np.mean(list(scores.values()))
        else:
            overall_score = scores.get(method, 0.0)
        
        # Determine match
        match_threshold = 0.6  # 60% similarity threshold
        match = bool(overall_score >= match_threshold)
        
        return match, overall_score, scores


# Global instance
_face_comparator = None

def get_face_comparator() -> FaceComparator:
    """Get or create global face comparator instance."""
    global _face_comparator
    if _face_comparator is None:
        _face_comparator = FaceComparator()
    return _face_comparator


def compare_passport_to_id(
    passport_img: Image.Image,
    id_card_img: Image.Image,
    method: str = 'ensemble'
) -> Tuple[Optional[bool], Optional[float], Dict[str, float]]:
    """
    Compare passport photo to ID card photo.
    
    Args:
        passport_img: Passport/portrait photo as PIL Image
        id_card_img: ID card image as PIL Image
        method: Comparison method ('histogram', 'ssim', 'features', 'ensemble')
        
    Returns:
        Tuple of (match_boolean, overall_score, detailed_scores_dict)
    """
    comparator = get_face_comparator()
    return comparator.compare_faces(passport_img, id_card_img, method=method)
