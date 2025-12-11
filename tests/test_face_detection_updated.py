"""
Test updated face detection
"""
import os
from pathlib import Path
from PIL import Image
import sys

sys.path.insert(0, str(Path(__file__).parent))

from verify import detect_faces

# Get test images
test_images = list(Path('training_data').rglob('*.jpg')) + list(Path('training_data').rglob('*.png'))

# Find a passport photo
passport_path = [p for p in test_images if 'passport' in str(p).lower()][0]
ghana_card_path = [p for p in test_images if 'GHANA' in str(p).upper()][0]

print("="*60)
print("Testing Face Detection")
print("="*60)

# Test 1: Passport photo (should have face)
print(f"\nTest 1: Passport Photo")
print(f"Image: {passport_path}")
passport_img = Image.open(passport_path)
print(f"Size: {passport_img.size}")

faces = detect_faces(passport_img)
print(f"Faces detected: {len(faces)}")
if faces:
    print("Face locations:")
    for i, (top, right, bottom, left) in enumerate(faces):
        print(f"  Face {i+1}: top={top}, right={right}, bottom={bottom}, left={left}")
        print(f"           width={right-left}, height={bottom-top}")
    print("[PASS] Face detection working!")
else:
    print("[FAIL] No faces detected in passport photo")

# Test 2: Ghana card (may have face)
print(f"\nTest 2: Ghana Card")
print(f"Image: {ghana_card_path}")
ghana_img = Image.open(ghana_card_path)
print(f"Size: {ghana_img.size}")

faces = detect_faces(ghana_img)
print(f"Faces detected: {len(faces)}")
if faces:
    print("Face locations:")
    for i, (top, right, bottom, left) in enumerate(faces):
        print(f"  Face {i+1}: top={top}, right={right}, bottom={bottom}, left={left}")
        print(f"           width={right-left}, height={bottom-top}")

print("\n" + "="*60)
print("Test Complete!")
print("="*60)
