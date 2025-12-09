"""
Advanced Face Detection for ID Cards
=====================================
Robust face detection with preprocessing for low quality/rotated images.
Includes face highlighting, extraction, and passport-size conversion.
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw
import io
import os

class IDCardFaceDetector:
    """
    Advanced face detector optimized for ID card images.
    Handles low quality, rotation, and various lighting conditions.
    """
    
    def __init__(self):
        """Initialize face detection models."""
        # Load OpenCV DNN face detector (more robust)
        model_dir = os.path.dirname(__file__)
        self.dnn_net = None
        
        # Try to load DNN model
        try:
            proto_path = os.path.join(model_dir, 'deploy.prototxt')
            model_path = os.path.join(model_dir, 'res10_300x300_ssd_iter_140000.caffemodel')
            
            # Download models if not present
            if not os.path.exists(proto_path) or not os.path.exists(model_path):
                self._download_dnn_models(model_dir)
            
            self.dnn_net = cv2.dnn.readNetFromCaffe(proto_path, model_path)
            print("✓ DNN face detector loaded")
        except Exception as e:
            print(f"⚠ DNN model not available: {e}")
        
        # Load Haar Cascade as fallback
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Load profile cascade for rotated faces
        self.profile_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_profileface.xml'
        )
        
        print("✓ ID Card Face Detector initialized")
    
    def _download_dnn_models(self, model_dir):
        """Download DNN face detection models."""
        import urllib.request
        
        print("Downloading DNN face detection models...")
        
        proto_url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
        model_url = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
        
        proto_path = os.path.join(model_dir, 'deploy.prototxt')
        model_path = os.path.join(model_dir, 'res10_300x300_ssd_iter_140000.caffemodel')
        
        try:
            urllib.request.urlretrieve(proto_url, proto_path)
            urllib.request.urlretrieve(model_url, model_path)
            print("✓ DNN models downloaded successfully")
        except Exception as e:
            print(f"⚠ Failed to download DNN models: {e}")
    
    def preprocess_image(self, img):
        """
        Preprocess image for better face detection.
        - Enhance contrast
        - Reduce noise
        - Auto-rotate if needed
        
        Args:
            img: OpenCV image (BGR)
        
        Returns:
            preprocessed: Enhanced image
            rotation_angle: Detected rotation angle
        """
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced)
        
        # Detect rotation
        rotation_angle = self._detect_rotation(img)
        
        # Rotate if needed
        if abs(rotation_angle) > 5:  # Only rotate if angle > 5 degrees
            img = self._rotate_image(img, rotation_angle)
            print(f"✓ Auto-rotated image by {rotation_angle:.1f}°")
        
        return img, rotation_angle
    
    def _detect_rotation(self, img):
        """Detect image rotation angle using text detection."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Use edge detection to find text orientation
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)
        
        if lines is None:
            return 0
        
        # Calculate average angle
        angles = []
        for rho, theta in lines[:, 0]:
            angle = np.degrees(theta) - 90
            if -45 < angle < 45:  # Only consider reasonable rotations
                angles.append(angle)
        
        if angles:
            return np.median(angles)
        return 0
    
    def _rotate_image(self, img, angle):
        """Rotate image by given angle."""
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        
        # Get rotation matrix
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Rotate image
        rotated = cv2.warpAffine(img, M, (w, h), 
                                 flags=cv2.INTER_CUBIC,
                                 borderMode=cv2.BORDER_REPLICATE)
        return rotated
    
    def detect_faces_robust(self, img, min_confidence=0.5):
        """
        Robust face detection using multiple methods.
        
        Args:
            img: OpenCV image (BGR) or PIL Image
            min_confidence: Minimum confidence for DNN detection
        
        Returns:
            faces: List of (x, y, w, h) face bounding boxes
            method: Detection method used
            preprocessed_img: Preprocessed image
        """
        # Convert PIL to OpenCV if needed
        if isinstance(img, Image.Image):
            img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # Preprocess image
        preprocessed, rotation = self.preprocess_image(img.copy())
        
        faces = []
        method = "none"
        
        # Method 1: DNN detector (most robust)
        if self.dnn_net is not None:
            faces, conf = self._detect_dnn(preprocessed, min_confidence)
            if len(faces) > 0:
                method = f"DNN (conf: {conf:.2f})"
                print(f"✓ Detected {len(faces)} face(s) using DNN")
                return faces, method, preprocessed
        
        # Method 2: Haar Cascade on enhanced image
        faces = self._detect_haar(preprocessed)
        if len(faces) > 0:
            method = "Haar Cascade"
            print(f"✓ Detected {len(faces)} face(s) using Haar Cascade")
            return faces, method, preprocessed
        
        # Method 3: Try different scales
        for scale in [1.1, 1.05, 1.15]:
            faces = self._detect_haar(preprocessed, scale_factor=scale)
            if len(faces) > 0:
                method = f"Haar (scale: {scale})"
                print(f"✓ Detected {len(faces)} face(s) using Haar at scale {scale}")
                return faces, method, preprocessed
        
        # Method 4: Profile detection (for rotated faces)
        faces = self._detect_profile(preprocessed)
        if len(faces) > 0:
            method = "Profile Cascade"
            print(f"✓ Detected {len(faces)} face(s) using Profile detection")
            return faces, method, preprocessed
        
        print("⚠ No faces detected with any method")
        return [], method, preprocessed
    
    def _detect_dnn(self, img, min_confidence=0.5):
        """Detect faces using DNN."""
        h, w = img.shape[:2]
        
        # Prepare blob
        blob = cv2.dnn.blobFromImage(
            cv2.resize(img, (300, 300)), 1.0,
            (300, 300), (104.0, 177.0, 123.0)
        )
        
        self.dnn_net.setInput(blob)
        detections = self.dnn_net.forward()
        
        faces = []
        max_conf = 0
        
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > min_confidence:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x, y, x2, y2) = box.astype("int")
                
                # Convert to (x, y, w, h)
                faces.append((x, y, x2 - x, y2 - y))
                max_conf = max(max_conf, confidence)
        
        return faces, max_conf
    
    def _detect_haar(self, img, scale_factor=1.1):
        """Detect faces using Haar Cascade."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=scale_factor,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        return list(faces)
    
    def _detect_profile(self, img):
        """Detect profile faces."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        faces = self.profile_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        return list(faces)
    
    def highlight_face(self, img, faces, color=(0, 255, 0), thickness=2):
        """
        Draw dotted bounding boxes around detected faces.
        
        Args:
            img: PIL Image or OpenCV image
            faces: List of (x, y, w, h) tuples
            color: RGB color for box
            thickness: Line thickness
        
        Returns:
            highlighted: PIL Image with boxes drawn
        """
        # Convert to PIL if needed
        if isinstance(img, np.ndarray):
            img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        # Create drawing context
        draw = ImageDraw.Draw(img)
        
        for (x, y, w, h) in faces:
            # Draw dotted rectangle
            self._draw_dotted_rectangle(draw, x, y, w, h, color, thickness)
            
            # Add label
            label = f"Face {w}x{h}"
            draw.text((x, y - 20), label, fill=color)
        
        return img
    
    def _draw_dotted_rectangle(self, draw, x, y, w, h, color, thickness):
        """Draw dotted rectangle."""
        dash_length = 10
        gap_length = 5
        
        # Top line
        for i in range(x, x + w, dash_length + gap_length):
            draw.line([(i, y), (min(i + dash_length, x + w), y)], 
                     fill=color, width=thickness)
        
        # Bottom line
        for i in range(x, x + w, dash_length + gap_length):
            draw.line([(i, y + h), (min(i + dash_length, x + w), y + h)], 
                     fill=color, width=thickness)
        
        # Left line
        for i in range(y, y + h, dash_length + gap_length):
            draw.line([(x, i), (x, min(i + dash_length, y + h))], 
                     fill=color, width=thickness)
        
        # Right line
        for i in range(y, y + h, dash_length + gap_length):
            draw.line([(x + w, i), (x + w, min(i + dash_length, y + h))], 
                     fill=color, width=thickness)
    
    def extract_face(self, img, face_box, padding=0.2):
        """
        Extract face region with padding.
        
        Args:
            img: OpenCV image or PIL Image
            face_box: (x, y, w, h) tuple
            padding: Percentage padding around face
        
        Returns:
            face_img: Extracted face as PIL Image
        """
        # Convert to OpenCV if needed
        if isinstance(img, Image.Image):
            img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        x, y, w, h = face_box
        
        # Add padding
        pad_w = int(w * padding)
        pad_h = int(h * padding)
        
        x1 = max(0, x - pad_w)
        y1 = max(0, y - pad_h)
        x2 = min(img.shape[1], x + w + pad_w)
        y2 = min(img.shape[0], y + h + pad_h)
        
        # Extract face region
        face_img = img[y1:y2, x1:x2]
        
        # Convert to PIL
        face_pil = Image.fromarray(cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB))
        
        return face_pil
    
    def convert_to_passport_size(self, face_img, size=(600, 600)):
        """
        Convert face to standard passport photo size.
        
        Args:
            face_img: PIL Image
            size: Target size (width, height)
        
        Returns:
            passport_img: Resized image
        """
        # Resize maintaining aspect ratio
        face_img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Create white background
        passport_img = Image.new('RGB', size, (255, 255, 255))
        
        # Center the face
        offset = ((size[0] - face_img.width) // 2,
                  (size[1] - face_img.height) // 2)
        
        passport_img.paste(face_img, offset)
        
        return passport_img
    
    def process_id_card(self, id_card_img, save_path=None):
        """
        Complete pipeline: detect, highlight, extract, and convert face from ID card.
        
        Args:
            id_card_img: PIL Image or path to image
            save_path: Optional path to save extracted face
        
        Returns:
            result: Dictionary with:
                - faces_detected: Number of faces
                - highlighted_img: Image with boxes
                - extracted_faces: List of passport-sized face images
                - method: Detection method used
                - success: Boolean
        """
        # Load image if path provided
        if isinstance(id_card_img, str):
            id_card_img = Image.open(id_card_img)
        
        # Convert to OpenCV
        cv_img = cv2.cvtColor(np.array(id_card_img), cv2.COLOR_RGB2BGR)
        
        # Detect faces
        faces, method, preprocessed = self.detect_faces_robust(cv_img)
        
        if len(faces) == 0:
            return {
                'faces_detected': 0,
                'highlighted_img': id_card_img,
                'extracted_faces': [],
                'method': method,
                'success': False,
                'message': 'No faces detected on ID card'
            }
        
        # Highlight faces
        highlighted = self.highlight_face(id_card_img, faces)
        
        # Extract and convert faces
        extracted_faces = []
        for i, face_box in enumerate(faces):
            # Extract face
            face_img = self.extract_face(cv_img, face_box)
            
            # Convert to passport size
            passport_img = self.convert_to_passport_size(face_img)
            
            extracted_faces.append(passport_img)
            
            # Save if path provided
            if save_path and i == 0:  # Save first (largest) face
                passport_img.save(save_path)
                print(f"✓ Saved extracted face to {save_path}")
        
        return {
            'faces_detected': len(faces),
            'highlighted_img': highlighted,
            'extracted_faces': extracted_faces,
            'face_boxes': faces,
            'method': method,
            'success': True,
            'message': f'Successfully detected {len(faces)} face(s) using {method}'
        }


def compare_faces_advanced(passport_img, extracted_face_img, threshold=0.6):
    """
    Compare passport photo with extracted ID face using multiple methods.
    
    Args:
        passport_img: PIL Image of passport photo
        extracted_face_img: PIL Image of extracted ID face
        threshold: Similarity threshold (0-1)
    
    Returns:
        result: Dictionary with match status and scores
    """
    from face_comparison import FaceComparator
    
    comparator = FaceComparator()
    
    # Use ensemble comparison method
    is_match, similarity, scores = comparator.compare_faces(
        passport_img, extracted_face_img, method='ensemble'
    )
    
    # Convert score to percentage
    if similarity is not None:
        similarity_pct = similarity * 100.0
        scores_pct = {k: v * 100.0 for k, v in scores.items()} if scores else {}
    else:
        similarity_pct = 0.0
        scores_pct = {}
    
    return {
        'match': is_match,
        'similarity': similarity_pct,
        'scores': scores_pct,
        'threshold': threshold,
        'message': f"{'✓ MATCH' if is_match else '✗ NO MATCH'} - Similarity: {similarity_pct:.1f}%"
    }


# Convenience function
def detect_and_extract_id_face(id_card_path, output_path='extracted_face.jpg'):
    """
    Quick function to detect and extract face from ID card.
    
    Args:
        id_card_path: Path to ID card image
        output_path: Where to save extracted face
    
    Returns:
        result: Detection result dictionary
    """
    detector = IDCardFaceDetector()
    result = detector.process_id_card(id_card_path, save_path=output_path)
    
    print(f"\n{'='*60}")
    print(f"ID Card Face Detection Results")
    print(f"{'='*60}")
    print(f"Faces detected: {result['faces_detected']}")
    print(f"Detection method: {result['method']}")
    print(f"Status: {result['message']}")
    print(f"{'='*60}\n")
    
    return result


if __name__ == "__main__":
    # Test the detector
    print("Testing ID Card Face Detector...")
    
    test_id = "training_data/GHANA CARDS/1.png"
    if os.path.exists(test_id):
        result = detect_and_extract_id_face(test_id)
        
        if result['success'] and result['extracted_faces']:
            # Show extracted face
            result['extracted_faces'][0].show()
            print("✓ Face extraction successful!")
    else:
        print(f"Test image not found: {test_id}")
