"""
Debug Gemini API response for card detection
"""
import os
from pathlib import Path
from PIL import Image
import base64
import io
import sys
import json

sys.path.insert(0, str(Path(__file__).parent))

import google.generativeai as genai

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("[FAIL] GEMINI_API_KEY not set")
    sys.exit(1)

genai.configure(api_key=api_key)

# Get test image
test_images = list(Path('training_data').rglob('*.jpg')) + list(Path('training_data').rglob('*.png'))
test_img_path = [p for p in test_images if 'GHANA' in str(p).upper()][0]
img = Image.open(test_img_path)

# Convert to base64
buffered = io.BytesIO()
img.save(buffered, format="JPEG")
img_base64 = base64.standard_b64encode(buffered.getvalue()).decode()

print(f"Image: {test_img_path}")
print(f"Base64 length: {len(img_base64)}")

# Test with exact same prompt as in gemini_card_detector.py
prompt = """Analyze this identification card image and determine its type.

Based on the card's appearance, text, colors, logos, and design patterns, identify the card type.

The possible card types are:
1. Ghana Card - Official national ID card of Ghana
2. Voter ID Card - Voter registration/identification card
3. Ghana Passport - Ghanaian passport book/document
4. Ghana Driver's License - Ghana vehicle driver's license
5. Other - Unknown or non-identification card

Respond with a JSON object in this exact format:
{
    "card_type": "[one of the 5 types above]",
    "confidence": [0.0 to 1.0],
    "reasoning": "[brief explanation of what you observed]"
}"""

print(f"\n" + "="*60)
print("Testing Gemini 2.5 Flash with card detection prompt")
print("="*60 + "\n")

model = genai.GenerativeModel('gemini-2.5-flash')

response = model.generate_content([
    prompt,
    {
        "mime_type": "image/jpeg",
        "data": img_base64
    }
])

print("RAW RESPONSE:")
print(response.text)
print("\n" + "="*60)

# Parse JSON
json_start = response.text.find('{')
json_end = response.text.rfind('}') + 1

if json_start != -1 and json_end > json_start:
    json_str = response.text[json_start:json_end]
    print("EXTRACTED JSON:")
    print(json_str)
    result = json.loads(json_str)
    print("\nPARSED:")
    print(f"  Card Type: {result.get('card_type')}")
    print(f"  Confidence: {result.get('confidence')}")
    print(f"  Reasoning: {result.get('reasoning')}")
else:
    print("FAILED TO EXTRACT JSON")
