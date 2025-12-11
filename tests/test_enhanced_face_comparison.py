"""
Test enhanced face comparison
"""
import os
from pathlib import Path
from PIL import Image
import sys

sys.path.insert(0, str(Path(__file__).parent))

from face_comparison import compare_passport_to_id, FaceComparator

# Get test images
test_images = list(Path('training_data').rglob('*.jpg')) + list(Path('training_data').rglob('*.png'))

# Find a Ghana card and passport photo
ghana_card_path = [p for p in test_images if 'GHANA' in str(p).upper()][0]
passport_path = [p for p in test_images if 'passport' in str(p).lower()][0]

print(f"Testing Enhanced Face Comparison")
print(f"=" * 60)
print(f"Ghana Card: {ghana_card_path}")
print(f"Passport: {passport_path}")
print()

ghana_card = Image.open(ghana_card_path)
passport = Image.open(passport_path)

print(f"Image sizes:")
print(f"  Ghana Card: {ghana_card.size}")
print(f"  Passport: {passport.size}")
print()

# Test with different methods
print("="*60)
print("Testing Face Comparison Methods")
print("="*60)

methods = ['histogram', 'features', 'ensemble']

for method in methods:
    print(f"\nMethod: {method.upper()}")
    print("-" * 40)
    
    match, score, details = compare_passport_to_id(ghana_card, passport, method=method)
    
    if match is None:
        print(f"  Result: Could not compare faces")
        print(f"  Details: {details}")
    else:
        print(f"  Match: {match}")
        print(f"  Overall Score: {score:.3f} ({score*100:.1f}%)")
        print(f"  Detailed Scores:")
        for detail_method, detail_score in details.items():
            print(f"    - {detail_method}: {detail_score:.3f} ({detail_score*100:.1f}%)")

# Test with SSIM if available
try:
    print(f"\nMethod: SSIM")
    print("-" * 40)
    match, score, details = compare_passport_to_id(ghana_card, passport, method='ssim')
    if match is not None:
        print(f"  Match: {match}")
        print(f"  Score: {score:.3f} ({score*100:.1f}%)")
except Exception as e:
    print(f"  SSIM not available: {e}")

print("\n" + "="*60)
print("Test Complete!")
print("="*60)
