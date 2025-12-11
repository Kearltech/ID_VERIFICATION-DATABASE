"""
Debug card detection issue
"""
import os
from pathlib import Path
from PIL import Image
import sys

sys.path.insert(0, str(Path(__file__).parent))

from gemini_card_detector import detect_card_type

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("[FAIL] GEMINI_API_KEY not set")
    sys.exit(1)

# Get test image
test_images = list(Path('training_data').rglob('*.jpg')) + list(Path('training_data').rglob('*.png'))
test_img_path = [p for p in test_images if 'GHANA' in str(p).upper()][0]
img = Image.open(test_img_path)

print(f"Testing detect_card_type directly")
print(f"Image: {test_img_path}")
print(f"API Key provided: {bool(api_key)}")
print(f"\nCalling detect_card_type(img, api_key=api_key)...")

card_type, confidence = detect_card_type(img, api_key=api_key)

print(f"\nResult:")
print(f"  Card Type: {card_type}")
print(f"  Confidence: {confidence:.1%}")

if card_type == 'Ghana Card':
    print("\n[PASS] Correctly detected Ghana Card!")
elif card_type == 'Other' and confidence == 1.0:
    print("\n[WARN] Got 'Other' with 100% confidence (should not happen)")
else:
    print(f"\n[WARN] Got '{card_type}' with {confidence:.1%}")
