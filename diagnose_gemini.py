"""
Diagnose available Gemini models and test API connectivity.
"""

import os

try:
    import google.generativeai as genai
except ImportError:
    print("ERROR: google-generativeai not installed")
    print("Run: pip install google-generativeai")
    exit(1)

print("=" * 70)
print("GEMINI API DIAGNOSTIC")
print("=" * 70)

# Check API key
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("\n⚠️  WARNING: GEMINI_API_KEY environment variable not set")
    print("   The app may fail if API key is not configured")
else:
    print(f"\n✓ GEMINI_API_KEY is set")
    genai.configure(api_key=api_key)

print("\n" + "=" * 70)
print("TESTING MODEL NAMES")
print("=" * 70)

model_names = [
    'gemini-1.5-flash',           # Correct format (v1beta)
    'models/gemini-1.5-flash',    # Incorrect format (v1)
    'gemini-1.5-pro',             # Alternative
    'gemini-pro',                 # Legacy
    'gemini-pro-vision',          # Legacy vision model
]

for model_name in model_names:
    try:
        print(f"\nTesting: {model_name}")
        model = genai.GenerativeModel(model_name)
        print(f"  ✓ Model loaded successfully")
        
        # Try to generate content with a simple text prompt
        response = model.generate_content("Hello")
        print(f"  ✓ Content generation works")
        print(f"  ✓ Response: {response.text[:50]}...")
        
    except Exception as e:
        error_msg = str(e)
        print(f"  ✗ Failed: {error_msg[:100]}")

print("\n" + "=" * 70)
print("TESTING WITH VISION (IMAGE) SUPPORT")
print("=" * 70)

from PIL import Image
import io

# Create a test image
img = Image.new('RGB', (100, 100), color='red')

# Convert to bytes
img_byte_arr = io.BytesIO()
img.save(img_byte_arr, format='PNG')
img_byte_arr.seek(0)

vision_models = [
    'gemini-1.5-flash',
    'gemini-pro-vision',
]

for model_name in vision_models:
    try:
        print(f"\nTesting vision with: {model_name}")
        model = genai.GenerativeModel(model_name)
        
        # Try to generate content with image
        response = model.generate_content([
            "What is in this image?",
            {"mime_type": "image/png", "data": img_byte_arr.getvalue()}
        ])
        print(f"  ✓ Vision API works")
        print(f"  ✓ Response: {response.text[:50]}...")
        
    except Exception as e:
        error_msg = str(e)
        print(f"  ✗ Failed: {error_msg[:100]}")

print("\n" + "=" * 70)
print("RECOMMENDATIONS")
print("=" * 70)

print("""
✓ CORRECT MODEL NAME: 'gemini-1.5-flash'
  (without the 'models/' prefix)

✗ INCORRECT: 'models/gemini-1.5-flash'
  (this format is for older API versions)

If gemini-1.5-flash is not available, use:
  - 'gemini-pro-vision' (for vision tasks)
  - 'gemini-pro' (for text tasks)

Make sure GEMINI_API_KEY environment variable is set!
""")

print("=" * 70)
