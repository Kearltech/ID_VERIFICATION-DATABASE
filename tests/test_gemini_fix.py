"""
Test script to verify Gemini API calls work with the corrected format
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
    print("❌ GEMINI_API_KEY not set in environment")
    sys.exit(1)

print("✓ API key found")

# Configure Gemini
if not configure_gemini(api_key):
    print("❌ Failed to configure Gemini")
    sys.exit(1)

print("✓ Gemini API configured")

# Find a test image
import glob
test_images = glob.glob('training_data/**/*.jpg', recursive=True) + glob.glob('training_data/**/*.png', recursive=True)

if not test_images:
    print("❌ No test images found in 'training_data' directory")
    sys.exit(1)

test_image_path = test_images[0]
print(f"✓ Using test image: {test_image_path}")

# Load image
try:
    pil_img = Image.open(test_image_path)
    print(f"✓ Image loaded: {pil_img.size}")
except Exception as e:
    print(f"❌ Failed to load image: {e}")
    sys.exit(1)

# Test 1: Card type detection
print("\n" + "="*60)
print("TEST 1: Card Type Detection")
print("="*60)

try:
    card_type, confidence = detect_card_type(pil_img, api_key=api_key)
    print(f"✓ Card Type: {card_type}")
    print(f"✓ Confidence: {confidence}")
    
    if card_type == 'Other' and confidence == 0.0:
        print("⚠️  WARNING: Got fallback 'Other' type with 0% confidence")
        print("    This may indicate the Gemini API call failed")
    else:
        print("✓ PASS: Card detection working correctly")
except Exception as e:
    print(f"❌ FAIL: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Text extraction
print("\n" + "="*60)
print("TEST 2: Text Extraction")
print("="*60)

try:
    result = extract_card_text(pil_img, card_type=card_type, api_key=api_key)
    
    if result['success']:
        print(f"✓ Extraction successful")
        print(f"✓ Fields found: {len(result['text_fields'])}")
        print(f"✓ Confidence: {result['confidence']}")
        
        # Display extracted fields
        if result['text_fields']:
            print("\nExtracted Fields:")
            for field, value in result['text_fields'].items():
                print(f"  - {field}: {value}")
        
        print("✓ PASS: Text extraction working correctly")
    else:
        print(f"⚠️  Extraction returned success=False: {result['message']}")
        
except Exception as e:
    print(f"❌ FAIL: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("All tests completed!")
print("="*60)
