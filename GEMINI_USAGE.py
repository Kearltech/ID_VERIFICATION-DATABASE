"""
Quick reference for using Gemini API in the ID Verification system.
"""

# =============================================================================
# BASIC USAGE EXAMPLES
# =============================================================================

from PIL import Image
from gemini_card_detector import (
    configure_gemini,
    detect_card_type,
    extract_card_text,
    analyze_card_complete
)

API_KEY = "<GEMINI_API_KEY>"

# Load an image
card_image = Image.open("path/to/card.jpg")

# ------- OPTION 1: Complete Analysis (Recommended) -------
# Detects card type AND extracts text in one call
result = analyze_card_complete(card_image, API_KEY)

print("Card Type:", result['card_type'])
print("Card Type Confidence:", result['card_type_confidence'])
print("Text Fields:", result['text_extraction']['text_fields'])
print("Raw OCR:", result['text_extraction']['raw_ocr'])

# ------- OPTION 2: Card Type Detection Only -------
card_type, confidence = detect_card_type(card_image, API_KEY)
print(f"Detected: {card_type} ({confidence*100:.1f}% confidence)")

# ------- OPTION 3: Text Extraction Only -------
extraction = extract_card_text(card_image, card_type="Ghana Card", api_key=API_KEY)
print("Extracted Fields:", extraction['text_fields'])
print("Success:", extraction['success'])

# ------- OPTION 4: Using Wrapper Functions from verify.py -------
from verify import analyze_card_gemini, detect_card_type_gemini, extract_card_text_gemini

result = analyze_card_gemini(card_image, API_KEY)
card_type, confidence = detect_card_type_gemini(card_image, API_KEY)
extraction = extract_card_text_gemini(card_image, api_key=API_KEY)

# =============================================================================
# RETURNED DATA STRUCTURES
# =============================================================================

# Card Type Detection returns:
# (card_type: str, confidence: float)
# card_type: one of 'Ghana Card', 'Voter ID Card', 'Ghana Passport', 
#            'Ghana Driver\'s License', 'Other'
# confidence: 0.0 to 1.0

# Text Extraction returns dict:
{
    "text_fields": {
        "name": "John Doe",
        "date_of_birth": "1990-05-15",
        "id_number": "GHA-123456789-0",
        # ... more fields
    },
    "raw_ocr": "Full text extracted from card...",
    "confidence": 0.85,
    "success": True,
    "message": "Text extraction successful",
    "notes": "Any additional observations"
}

# Complete Analysis returns dict:
{
    "card_type": "Ghana Card",
    "card_type_confidence": 0.95,
    "text_extraction": {
        # ... same as above
    },
    "success": True,
    "message": "Analysis complete"
}

# =============================================================================
# RUNNING THE STREAMLIT APP
# =============================================================================

# Activate environment:
# .venv\Scripts\Activate.ps1

# Install dependencies:
# pip install -r requirements.txt

# Run the Gemini-enhanced app:
# python -m streamlit run app_gemini.py

# The app will:
# 1. Ask for your Gemini API key
# 2. Allow you to upload a portrait and ID card
# 3. Automatically detect card type using Gemini Vision
# 4. Extract all text fields based on labels
# 5. Validate against manual entry
# 6. Compare face from portrait with ID card
# 7. Save results to submissions.csv

# =============================================================================
# EXPECTED OUTPUT FOR DIFFERENT CARD TYPES
# =============================================================================

# GHANA CARD (National ID)
# Expected fields might include:
# - name / surname / firstname
# - date_of_birth
# - id_number (format: GHA-000000000-0)
# - sex / gender
# - nationality
# - issuing_authority
# - expiry_date
# - address

# VOTER ID CARD
# Expected fields might include:
# - surname / firstname
# - date_of_birth
# - voter_id_number (10 digits)
# - registration_date
# - registration_area
# - constituency

# GHANA DRIVER'S LICENSE
# Expected fields might include:
# - surname / firstname / name
# - date_of_birth
# - license_number
# - driving_class
# - expiry_date
# - address
# - nationality

# GHANA PASSPORT
# Expected fields might include:
# - surname / firstname
# - date_of_birth
# - passport_number
# - sex
# - nationality
# - place_of_birth
# - date_of_issue
# - date_of_expiry

# =============================================================================
# ERROR HANDLING
# =============================================================================

try:
    result = analyze_card_complete(card_image, API_KEY)
    if result['success']:
        # Process successful result
        fields = result['text_extraction']['text_fields']
    else:
        # Handle error
        print(f"Error: {result['message']}")
except Exception as e:
    print(f"Exception: {e}")

# Common issues:
# 1. API Key Invalid: "Failed to configure Gemini API"
#    -> Check your API key at https://aistudio.google.com/app/apikeys
#
# 2. Image quality: Low confidence or missing fields
#    -> Ensure clear, well-lit image of the card
#    -> Card should be straight and in focus
#
# 3. Unsupported card type: card_type returns "Other"
#    -> Card type may not be recognized
#    -> Try uploading a clearer image
#    -> You can still manually select the type

# =============================================================================
# INTEGRATING WITH YOUR APPLICATION
# =============================================================================

from verify import analyze_card_gemini

# In your app
if uploaded_card_image:
    analysis = analyze_card_gemini(uploaded_card_image, api_key)
    
    if analysis['success']:
        # Use detected card type
        auto_detected_type = analysis['card_type']
        
        # Use extracted text to pre-fill form
        text_fields = analysis['text_extraction']['text_fields']
        form_data = {
            'id_number': text_fields.get('id_number', ''),
            'name': text_fields.get('name', ''),
            'date_of_birth': text_fields.get('date_of_birth', ''),
            # ... map other fields
        }
        
        # Display confidence
        confidence = analysis['card_type_confidence']
        if confidence < 0.7:
            show_warning("Low confidence in card type detection. Please verify manually.")

# =============================================================================

