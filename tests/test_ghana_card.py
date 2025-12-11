"""
Test the corrected Gemini API with Ghana card images
"""

import os
import json
from pathlib import Path
from PIL import Image
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure API
from gemini_card_detector import configure_gemini, detect_card_type, extract_card_text
from logger_config import audit_logger

# Get API key from environment
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("[FAIL] GEMINI_API_KEY not set in environment")
    sys.exit(1)

print("[OK] API key found")

# Configure Gemini
if not configure_gemini(api_key):
    print("[FAIL] Failed to configure Gemini")
    sys.exit(1)

print("[OK] Gemini API configured")

# Test with Ghana Card
ghana_card_path = Path('training_data/GHANA CARDS/1.png')

if not ghana_card_path.exists():
    print(f"[FAIL] Test image not found: {ghana_card_path}")
    sys.exit(1)

# Load image
try:
    pil_img = Image.open(ghana_card_path)
    print(f"[OK] Ghana card loaded: {pil_img.size}")
except Exception as e:
    print(f"[FAIL] Failed to load image: {e}")
    sys.exit(1)

# Test 1: Card type detection
print("\n" + "="*60)
print("TEST 1: Ghana Card Type Detection")
print("="*60)

try:
    card_type, confidence = detect_card_type(pil_img, api_key=api_key)
    print(f"[OK] Card Type: {card_type}")
    print(f"[OK] Confidence: {confidence:.2%}")
    
    if card_type == 'Ghana Card' and confidence > 0.5:
        print("[PASS] Correctly identified as Ghana Card")
    else:
        print(f"[WARN] Got '{card_type}' with {confidence:.2%} confidence")
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()

# Test 2: Text extraction
print("\n" + "="*60)
print("TEST 2: Ghana Card Text Extraction")
print("="*60)

try:
    result = extract_card_text(pil_img, card_type=card_type, api_key=api_key)
    
    if result['success']:
        print(f"[OK] Extraction successful")
        print(f"[OK] Fields found: {len(result['text_fields'])}")
        print(f"[OK] Confidence: {result['confidence']:.2%}")
        
        # Display extracted fields
        if result['text_fields']:
            print("\nExtracted Fields:")
            for field, value in result['text_fields'].items():
                print(f"  - {field}: {value}")
        
        print("[PASS] Text extraction working correctly")
    else:
        print(f"[WARN] Extraction returned success=False: {result['message']}")
        
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()

# Test with ML model for comparison
print("\n" + "="*60)
print("TEST 3: ML Model Comparison")
print("="*60)

try:
    from trained_model_predictor import predict_card_type, is_model_ready
    
    if is_model_ready():
        print("[OK] ML Model is ready")
        
        ml_type, ml_confidence = predict_card_type(pil_img)
        print(f"[OK] ML Model Type: {ml_type}")
        print(f"[OK] ML Model Confidence: {ml_confidence:.2%}")
        
        if ml_type == 'Ghana Card':
            print("[PASS] ML model also correctly identified as Ghana Card")
        else:
            print(f"[WARN] ML model got '{ml_type}'")
    else:
        print("[WARN] ML Model not ready")
        
except Exception as e:
    print(f"[WARN] ML Model test skipped: {e}")

print("\n" + "="*60)
print("All tests completed!")
print("="*60)
