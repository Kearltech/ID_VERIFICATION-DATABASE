"""
Integration module for trained card detection models.
Provides inference functions using trained models with fallback to Gemini API.
"""

import pickle
import json
import logging
from pathlib import Path
from typing import Dict, Tuple
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

# Model paths
MODEL_DIR = Path('models')
MODEL_PATH = MODEL_DIR / 'card_type_detector.pkl'
ENCODER_PATH = MODEL_DIR / 'label_encoder.pkl'
FIELD_PATTERNS_PATH = MODEL_DIR / 'field_patterns.json'
HISTORY_PATH = MODEL_DIR / 'training_history.json'

class TrainedModelPredictor:
    """Use trained models for inference."""
    
    def __init__(self):
        self.model = None
        self.label_encoder = None
        self.field_patterns = None
        self.training_history = None
        self.load_models()
    
    def load_models(self) -> bool:
        """Load trained models from disk."""
        try:
            if MODEL_PATH.exists():
                with open(MODEL_PATH, 'rb') as f:
                    self.model = pickle.load(f)
                logger.info("✓ Loaded card type detector model")
            
            if ENCODER_PATH.exists():
                with open(ENCODER_PATH, 'rb') as f:
                    self.label_encoder = pickle.load(f)
                logger.info("✓ Loaded label encoder")
            
            if FIELD_PATTERNS_PATH.exists():
                with open(FIELD_PATTERNS_PATH, 'r') as f:
                    self.field_patterns = json.load(f)
                logger.info(f"✓ Loaded field patterns for {len(self.field_patterns)} card types")
            
            if HISTORY_PATH.exists():
                with open(HISTORY_PATH, 'r') as f:
                    self.training_history = json.load(f)
                logger.info(f"✓ Training accuracy: {self.training_history['accuracy'][0]:.4f}")
            
            return self.model is not None
        
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
    
    def extract_image_features(self, image_path: str) -> np.ndarray:
        """Extract features from image for prediction."""
        try:
            if isinstance(image_path, str):
                img = Image.open(image_path)
            else:
                img = image_path  # Assume PIL Image
            
            # Resize for consistency
            img = img.resize((224, 224))
            
            # Convert to array
            img_array = np.array(img)
            
            # If grayscale, convert to RGB
            if len(img_array.shape) == 2:
                img_array = np.stack([img_array] * 3, axis=-1)
            
            # Extract features (same as training)
            features = []
            
            # 1. Color histogram
            for channel in range(min(3, img_array.shape[2] if len(img_array.shape) > 2 else 1)):
                hist = np.histogram(img_array[:,:,channel] if len(img_array.shape) > 2 else img_array, bins=32)[0]
                features.extend(hist)
            
            # 2. Mean and std
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2)
            else:
                gray = img_array
            
            features.append(np.mean(gray))
            features.append(np.std(gray))
            
            # 3. Edge density
            edges = np.abs(np.diff(gray, axis=0)).mean() + np.abs(np.diff(gray, axis=1)).mean()
            features.append(edges)
            
            # 4. Ratio
            h, w = gray.shape
            features.append(w / (h + 1))
            
            return np.array(features, dtype=np.float32).reshape(1, -1)
        
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return None
    
    def predict_card_type(self, image_path) -> Tuple[str, float]:
        """
        Predict card type using trained model.
        
        Returns:
            (card_type, confidence)
        """
        if self.model is None or self.label_encoder is None:
            logger.warning("Trained model not available")
            return 'Other', 0.0
        
        try:
            features = self.extract_image_features(image_path)
            if features is None:
                return 'Other', 0.0
            
            # Predict
            predicted_label = self.model.predict(features)[0]
            probabilities = self.model.predict_proba(features)[0]
            confidence = float(np.max(probabilities))
            
            # Decode label
            card_type = self.label_encoder.inverse_transform([predicted_label])[0]
            
            logger.info(f"Predicted: {card_type} (confidence: {confidence:.4f})")
            return card_type, confidence
        
        except Exception as e:
            logger.error(f"Error predicting card type: {e}")
            return 'Other', 0.0
    
    def get_expected_fields(self, card_type: str) -> Dict[str, str]:
        """Get expected text fields for a card type."""
        if self.field_patterns is None:
            return {}
        
        return self.field_patterns.get(card_type, {})
    
    def get_training_stats(self) -> Dict:
        """Get training statistics."""
        if self.training_history is None:
            return {}
        
        return {
            'accuracy': self.training_history['accuracy'][0],
            'samples_per_class': self.training_history['samples_per_class'],
            'total_samples': self.training_history['total_samples']
        }
    
    def is_ready(self) -> bool:
        """Check if models are ready for inference."""
        return self.model is not None and self.label_encoder is not None


# Global predictor instance
_predictor = None

def get_predictor() -> TrainedModelPredictor:
    """Get or create the predictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = TrainedModelPredictor()
    return _predictor

def predict_card_type(image_path) -> Tuple[str, float]:
    """
    Predict card type from image.
    
    Args:
        image_path: Path to image file or PIL Image
    
    Returns:
        (card_type, confidence)
    """
    predictor = get_predictor()
    return predictor.predict_card_type(image_path)

def get_expected_fields(card_type: str) -> Dict[str, str]:
    """Get expected fields for a card type."""
    predictor = get_predictor()
    return predictor.get_expected_fields(card_type)

def is_model_ready() -> bool:
    """Check if trained models are available."""
    predictor = get_predictor()
    return predictor.is_ready()

def get_model_info() -> Dict:
    """Get information about trained models."""
    predictor = get_predictor()
    return {
        'ready': predictor.is_ready(),
        'training_stats': predictor.get_training_stats(),
        'model_path': str(MODEL_PATH),
        'encoder_path': str(ENCODER_PATH),
        'field_patterns_path': str(FIELD_PATTERNS_PATH)
    }
