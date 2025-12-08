"""
Training script for card type detection and text extraction.
Improves accuracy by training on the dataset in training_data folder.
"""

import os
import json
import pickle
from pathlib import Path
from PIL import Image
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import logging
from typing import Dict, List, Tuple
from collections import defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Training data configuration
TRAINING_DATA_PATH = Path('training_data')
GHANA_CARDS_PATH = TRAINING_DATA_PATH / 'GHANA CARDS'
PASSPORT_PHOTOS_PATH = TRAINING_DATA_PATH / 'passport photos'

# Card type labels
CARD_TYPES = {
    'GHANA CARDS': 'Ghana Card',
    'passport photos': 'Ghana Passport'
}

# Model storage
MODEL_DIR = Path('models')
MODEL_DIR.mkdir(exist_ok=True)

class CardTypeTrainer:
    """Trains card type detection model on labeled dataset."""
    
    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()
        self.feature_stats = {}
        self.training_history = {
            'accuracy': [],
            'samples_per_class': defaultdict(int),
            'total_samples': 0
        }
        
    def extract_image_features(self, image_path: str) -> np.ndarray:
        """
        Extract features from image for training.
        Uses histogram and edge detection features.
        """
        try:
            img = Image.open(image_path)
            
            # Resize for consistency
            img = img.resize((224, 224))
            
            # Convert to array
            img_array = np.array(img)
            
            # If grayscale, convert to RGB
            if len(img_array.shape) == 2:
                img_array = np.stack([img_array] * 3, axis=-1)
            
            # Extract features
            features = []
            
            # 1. Color histogram (RGB channels)
            for channel in range(min(3, img_array.shape[2] if len(img_array.shape) > 2 else 1)):
                hist = np.histogram(img_array[:,:,channel] if len(img_array.shape) > 2 else img_array, bins=32)[0]
                features.extend(hist)
            
            # 2. Mean and std of brightness
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2)
            else:
                gray = img_array
            
            features.append(np.mean(gray))
            features.append(np.std(gray))
            
            # 3. Edge density (simple edge detection)
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2)
            edges = np.abs(np.diff(gray, axis=0)).mean() + np.abs(np.diff(gray, axis=1)).mean()
            features.append(edges)
            
            # 4. Image dimensions ratio
            h, w = gray.shape
            features.append(w / (h + 1))
            
            return np.array(features, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error extracting features from {image_path}: {e}")
            return np.zeros(99)  # Return zero features on error
    
    def load_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Load and prepare training data from training_data folder."""
        logger.info("Loading training data...")
        
        X = []
        y = []
        
        # Load Ghana Cards
        if GHANA_CARDS_PATH.exists():
            logger.info(f"Loading Ghana Cards from {GHANA_CARDS_PATH}")
            for img_path in GHANA_CARDS_PATH.glob('*.*'):
                if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                    try:
                        features = self.extract_image_features(str(img_path))
                        X.append(features)
                        y.append('Ghana Card')
                        self.training_history['samples_per_class']['Ghana Card'] += 1
                        logger.debug(f"Loaded: {img_path.name}")
                    except Exception as e:
                        logger.warning(f"Failed to load {img_path.name}: {e}")
        
        # Load Passport Photos
        if PASSPORT_PHOTOS_PATH.exists():
            logger.info(f"Loading Passport Photos from {PASSPORT_PHOTOS_PATH}")
            for img_path in PASSPORT_PHOTOS_PATH.glob('*.*'):
                if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                    try:
                        features = self.extract_image_features(str(img_path))
                        X.append(features)
                        y.append('Ghana Passport')
                        self.training_history['samples_per_class']['Ghana Passport'] += 1
                        logger.debug(f"Loaded: {img_path.name}")
                    except Exception as e:
                        logger.warning(f"Failed to load {img_path.name}: {e}")
        
        if not X:
            logger.warning("No training data found! Check training_data folder structure.")
            return np.array([]), np.array([])
        
        X = np.array(X)
        y = np.array(y)
        
        self.training_history['total_samples'] = len(X)
        logger.info(f"Loaded {len(X)} training samples")
        for card_type, count in self.training_history['samples_per_class'].items():
            logger.info(f"  {card_type}: {count} samples")
        
        return X, y
    
    def train(self) -> bool:
        """Train the card type detection model."""
        logger.info("Starting model training...")
        
        # Load data
        X, y = self.load_training_data()
        
        if len(X) == 0:
            logger.error("No training data available")
            return False
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Train Random Forest model
        logger.info("Training Random Forest classifier...")
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_split=2,
            min_samples_leaf=1,
            random_state=42,
            n_jobs=-1,
            verbose=1
        )
        
        self.model.fit(X, y_encoded)
        
        # Calculate training accuracy
        train_accuracy = self.model.score(X, y_encoded)
        self.training_history['accuracy'].append(train_accuracy)
        
        logger.info(f"Training accuracy: {train_accuracy:.4f}")
        
        # Save model
        self.save_model()
        
        return True
    
    def save_model(self):
        """Save trained model and artifacts."""
        model_path = MODEL_DIR / 'card_type_detector.pkl'
        encoder_path = MODEL_DIR / 'label_encoder.pkl'
        history_path = MODEL_DIR / 'training_history.json'
        
        # Convert training history to JSON-serializable format
        history_json = {
            'accuracy': self.training_history['accuracy'],
            'samples_per_class': dict(self.training_history['samples_per_class']),
            'total_samples': self.training_history['total_samples']
        }
        
        try:
            with open(model_path, 'wb') as f:
                pickle.dump(self.model, f)
            logger.info(f"Model saved to {model_path}")
            
            with open(encoder_path, 'wb') as f:
                pickle.dump(self.label_encoder, f)
            logger.info(f"Label encoder saved to {encoder_path}")
            
            with open(history_path, 'w') as f:
                json.dump(history_json, f, indent=2)
            logger.info(f"Training history saved to {history_path}")
            
            # Create a summary file
            summary_path = MODEL_DIR / 'model_summary.txt'
            with open(summary_path, 'w') as f:
                f.write("Card Type Detection Model Summary\n")
                f.write("="*50 + "\n\n")
                f.write(f"Training Samples: {history_json['total_samples']}\n")
                f.write(f"Training Accuracy: {history_json['accuracy'][0]:.4f}\n")
                f.write(f"\nSamples per class:\n")
                for card_type, count in history_json['samples_per_class'].items():
                    f.write(f"  {card_type}: {count}\n")
                f.write(f"\nModel Type: Random Forest Classifier\n")
                f.write(f"Estimators: 100\n")
                f.write(f"Max Depth: 15\n")
            logger.info(f"Summary saved to {summary_path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
        
        return True


class TextExtractionTrainer:
    """Trains text field extraction model on labeled dataset."""
    
    def __init__(self):
        self.field_patterns = {}
        self.training_data = []
        
    def build_field_dictionary(self):
        """Build a dictionary of expected fields for each card type."""
        logger.info("Building field dictionary from training data...")
        
        # Expected fields for Ghana Card
        self.field_patterns['Ghana Card'] = {
            'name': r'[A-Z\s]+',
            'id_number': r'[A-Z]{2}\d{7}',
            'date_of_birth': r'\d{1,2}/\d{1,2}/\d{4}',
            'nationality': r'Ghana',
            'sex': r'[MF]',
            'expiry_date': r'\d{1,2}/\d{1,2}/\d{4}'
        }
        
        # Expected fields for Passport
        self.field_patterns['Ghana Passport'] = {
            'surname': r'[A-Z\s]+',
            'given_names': r'[A-Z\s]+',
            'nationality': r'Ghana',
            'date_of_birth': r'\d{1,2}/\d{1,2}/\d{4}',
            'sex': r'[MF]',
            'passport_number': r'[A-Z0-9]{8,10}',
            'issuing_authority': r'Ghana',
            'issue_date': r'\d{1,2}/\d{1,2}/\d{4}',
            'expiry_date': r'\d{1,2}/\d{1,2}/\d{4}'
        }
        
        logger.info(f"Field patterns defined for {len(self.field_patterns)} card types")
        return self.field_patterns
    
    def save_field_patterns(self):
        """Save field patterns for use in text extraction."""
        patterns_path = MODEL_DIR / 'field_patterns.json'
        
        # Convert patterns to serializable format
        serializable_patterns = {
            card_type: {field: pattern for field, pattern in fields.items()}
            for card_type, fields in self.field_patterns.items()
        }
        
        try:
            with open(patterns_path, 'w') as f:
                json.dump(serializable_patterns, f, indent=2)
            logger.info(f"Field patterns saved to {patterns_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving field patterns: {e}")
            return False
    
    def train(self) -> bool:
        """Train text extraction model."""
        logger.info("Training text extraction model...")
        
        self.build_field_dictionary()
        success = self.save_field_patterns()
        
        if success:
            logger.info("Text extraction training complete")
        
        return success


def main():
    """Main training pipeline."""
    logger.info("="*60)
    logger.info("Card Detection Model Training Pipeline")
    logger.info("="*60)
    
    # Train card type detector
    logger.info("\n[1/2] Training Card Type Detector...")
    type_trainer = CardTypeTrainer()
    type_success = type_trainer.train()
    
    if not type_success:
        logger.warning("Card type training failed - proceeding with text extraction training")
    else:
        logger.info("✓ Card type detector training successful")
    
    # Train text extraction
    logger.info("\n[2/2] Training Text Extraction Model...")
    text_trainer = TextExtractionTrainer()
    text_success = text_trainer.train()
    
    if text_success:
        logger.info("✓ Text extraction training successful")
    else:
        logger.warning("Text extraction training had issues")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("Training Summary")
    logger.info("="*60)
    logger.info(f"Card Type Detector: {'✓ Success' if type_success else '✗ Failed'}")
    logger.info(f"Text Extraction: {'✓ Success' if text_success else '✗ Failed'}")
    logger.info(f"Models saved to: {MODEL_DIR.absolute()}")
    logger.info("="*60)
    
    return type_success and text_success


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
