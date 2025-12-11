"""
Diagnostic script to test Gemini API with different formats
"""

import os
import google.generativeai as genai
from pathlib import Path
from PIL import Image
import base64
import sys

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("❌ GEMINI_API_KEY not set")
    sys.exit(1)

genai.configure(api_key=api_key)

# Get a test image
test_images = list(Path('training_data').rglob('*.jpg')) + list(Path('training_data').rglob('*.png'))
if not test_images:
    print("❌ No test images found")
    sys.exit(1)

test_image_path = test_images[0]
print(f"Using test image: {test_image_path}")

# Load and encode image
img = Image.open(test_image_path)
import io
buffered = io.BytesIO()
img.save(buffered, format="JPEG")
img_base64 = base64.standard_b64encode(buffered.getvalue()).decode()

print(f"\nImage loaded: {img.size}, Base64 length: {len(img_base64)}")

# Test different API call formats
models_to_test = ['gemini-1.5-flash', 'gemini-pro-vision', 'gemini-pro']

for model_name in models_to_test:
    print(f"\n" + "="*60)
    print(f"Testing model: {model_name}")
    print("="*60)
    
    try:
        # Load model
        print(f"Loading model...", end=" ")
        model = genai.GenerativeModel(model_name)
        print("✓")
        
        # Test 1: Simple text prompt
        print(f"Testing simple text prompt...", end=" ")
        try:
            response = model.generate_content("What is 2+2?")
            print(f"✓ Response: {response.text[:50]}...")
        except Exception as e:
            print(f"✗ Error: {str(e)[:100]}")
        
        # Test 2: Text + Image using list format
        print(f"Testing text+image with list format...", end=" ")
        try:
            response = model.generate_content([
                "What type of ID card is this?",
                {
                    "mime_type": "image/jpeg",
                    "data": img_base64
                }
            ])
            print(f"✓ Response: {response.text[:50]}...")
        except Exception as e:
            error_str = str(e)
            print(f"✗ Error: {error_str[:100]}")
            # Check if "models/" appears in error
            if "models/" in error_str:
                print("    ⚠️  SDK might be adding 'models/' prefix internally")
        
        # Test 3: Using model.generate_content with different structure
        print(f"Testing with genai.upload_file approach...", end=" ")
        try:
            # This is the FILE upload approach
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                img.save(tmp.name)
                tmp_path = tmp.name
            
            uploaded_file = genai.upload_file(tmp_path)
            response = model.generate_content([
                "What type of ID card is this?",
                uploaded_file
            ])
            print(f"✓ Response: {response.text[:50]}...")
            genai.delete_file(uploaded_file.name)
            os.unlink(tmp_path)
        except Exception as e:
            error_str = str(e)
            print(f"✗ Error: {error_str[:80]}")
            
    except Exception as e:
        print(f"✗ Failed to load model: {e}")

print("\n" + "="*60)
print("Diagnostic complete")
print("="*60)
