"""
Diagnostic script for face matching
"""
import os
from pathlib import Path
from PIL import Image
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

# Check OpenCV
try:
    import cv2
    print("[OK] OpenCV (cv2) available")
except Exception as e:
    print(f"[FAIL] OpenCV not available: {e}")
    sys.exit(1)

from verify import face_match, detect_faces

# Get test images
test_images = list(Path('training_data').rglob('*.jpg')) + list(Path('training_data').rglob('*.png'))

# Find a Ghana card
ghana_card_path = [p for p in test_images if 'GHANA' in str(p).upper()][0]
# Find a passport photo
passport_path = [p for p in test_images if 'passport' in str(p).lower()][0]

print(f"\nGhana Card: {ghana_card_path}")
print(f"Passport Photo: {passport_path}")

ghana_card = Image.open(ghana_card_path)
passport_img = Image.open(passport_path)

print(f"\nImage sizes:")
print(f"  Ghana Card: {ghana_card.size}")
print(f"  Passport: {passport_img.size}")

# Test 1: Detect faces in both images
print("\n" + "="*60)
print("TEST 1: Face Detection")
print("="*60)

faces_ghana = detect_faces(ghana_card)
faces_passport = detect_faces(passport_img)

print(f"Faces in Ghana Card: {len(faces_ghana)}")
print(f"Faces in Passport: {len(faces_passport)}")

# Test 2: Manual face encoding
print("\n" + "="*60)
print("TEST 2: Manual Face Encoding")
print("="*60)

ghana_arr = np.array(ghana_card)
passport_arr = np.array(passport_img)

print(f"Ghana Card array shape: {ghana_arr.shape}")
print(f"Passport array shape: {passport_arr.shape}")

try:
    import face_recognition
    ghana_encs = face_recognition.face_encodings(ghana_arr)
    print(f"Ghana Card face encodings found: {len(ghana_encs)}")
except Exception as e:
    print(f"face_recognition not available (using OpenCV instead): {e}")

try:
    import face_recognition
    passport_encs = face_recognition.face_encodings(passport_arr)
    print(f"Passport face encodings found: {len(passport_encs)}")
except Exception as e:
    print(f"face_recognition not available (using OpenCV instead): {e}")

# Test 3: Face matching
print("\n" + "="*60)
print("TEST 3: Face Matching")
print("="*60)

match, dist = face_match(ghana_card, passport_img)
print(f"Match result: {match}")
print(f"Distance: {dist}")

if match is None:
    print("\n[ISSUE] Face matching returned (None, None)")
    print("Possible causes:")
    print("  1. No faces found in one or both images")
    print("  2. face_recognition library issue")
    print("  3. Image format issue")
else:
    if match:
        print("\n[OK] Faces match!")
    else:
        print("\n[OK] Faces do not match (expected - different people)")
