"""
Test card detection fix
"""
import os
from pathlib import Path
from PIL import Image
import sys

sys.path.insert(0, str(Path(__file__).parent))

from gemini_card_detector import configure_gemini, analyze_card_complete

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("[FAIL] GEMINI_API_KEY not set")
    sys.exit(1)

# Get test image
test_images = list(Path('training_data').rglob('*.jpg')) + list(Path('training_data').rglob('*.png'))
if not test_images:
    print("[FAIL] No test images found")
    sys.exit(1)

test_img_path = [p for p in test_images if 'GHANA' in str(p).upper()][0]
img = Image.open(test_img_path)

print(f"[OK] Test image: {test_img_path}")
print(f"[OK] Image size: {img.size}")

# Test analyze_card_complete which should call detect_card_type with api_key
print("\n" + "="*60)
print("TEST: analyze_card_complete with api_key parameter")
print("="*60)

result = analyze_card_complete(img, api_key)

print(f"Card Type: {result.get('card_type')}")
print(f"Card Confidence: {result.get('card_type_confidence'):.1%}")
print(f"Text Extraction Success: {result.get('text_extraction', {}).get('success')}")
print(f"Overall Success: {result.get('success')}")

if result.get('card_type') != 'Other' or result.get('card_type_confidence') > 0.5:
    print("\n[PASS] Card detection working!")
else:
    print("\n[FAIL] Card detection not working")
    print(f"Message: {result.get('message')}")
