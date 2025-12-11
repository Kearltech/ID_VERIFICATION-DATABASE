# ID Verification System with Gemini Vision API

## Overview

This project provides an automated identification card verification system using **Google's Gemini Vision API** for:

1. **Card Type Detection** - Identifies if the card is a Ghana Card, Voter ID, Passport, Driver's License, or other type
2. **Text Extraction (OCR)** - Automatically extracts labeled text fields from the card (Name, Date of Birth, ID Number, etc.)
3. **Face Matching** - Compares the portrait with the ID card photo
4. **Validation** - Cross-references extracted data with manual entry and validation rules

## Key Features

✅ **Gemini Vision API Integration** - Uses advanced AI for accurate card detection and OCR
✅ **Automatic Field Extraction** - Reads and maps labeled fields from cards
✅ **Multi-Card Support** - Handles Ghana Card, Voter ID, Passport, and Driver's License
✅ **Face Recognition** - Matches portrait with ID card
✅ **Streamlit Web Interface** - Easy-to-use interactive application
✅ **Data Persistence** - Saves all submissions to CSV
✅ **Flexible Architecture** - Use individual functions or complete analysis

## Installation

### Prerequisites
- Python 3.8+
- Google Gemini API Key (free at https://aistudio.google.com/app/apikeys)

### Setup Steps

#### Windows PowerShell

```powershell
# Clone or navigate to project directory
cd C:\Users\ABY\Desktop\ML

# Create virtual environment
python -m venv .venv

# Activate environment
.venv\Scripts\Activate.ps1

# Upgrade pip
.venv\Scripts\python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# For face recognition (optional, can be tricky on Windows):
# pip install face_recognition opencv-python
```

## Configuration

### Get Your Gemini API Key

1. Go to https://aistudio.google.com/app/apikeys
2. Click "Create API Key"
3. Copy the key (keep it secret!)
4. Use it in the app when prompted

## Usage

### Option 1: Streamlit Web App (Recommended)

```powershell
# Activate environment
.venv\Scripts\Activate.ps1

# Run Gemini-enhanced app
python -m streamlit run app_gemini.py
```

Then:
1. Enter your Gemini API Key in the sidebar
2. Upload a portrait photo
3. Upload an ID card image
4. The app will automatically:
   - Detect the card type
   - Extract all text fields
   - Show extracted data
5. Optionally enter manual details for validation
6. Review validation results and face matching
7. Save the submission

### Option 2: Python Script Usage

```python
from PIL import Image
from gemini_card_detector import analyze_card_complete

# Load card image
card_image = Image.open("ghana_card.jpg")

# Analyze the card
result = analyze_card_complete(card_image, api_key="YOUR_API_KEY")

# Access results
print("Card Type:", result['card_type'])
print("Detected Fields:", result['text_extraction']['text_fields'])
print("Raw OCR:", result['text_extraction']['raw_ocr'])
```

### Option 3: Using Wrapper Functions

```python
from verify import analyze_card_gemini, detect_card_type_gemini, extract_card_text_gemini
from PIL import Image

card_img = Image.open("card.jpg")
api_key = "YOUR_API_KEY"

# Complete analysis
result = analyze_card_gemini(card_img, api_key)

# Or separately
card_type, confidence = detect_card_type_gemini(card_img, api_key)
text_data = extract_card_text_gemini(card_img, card_type=card_type, api_key=api_key)
```

## Project Structure

```
ML/
├── app.py                      # Original Streamlit app
├── app_gemini.py              # Enhanced Streamlit app with Gemini integration
├── verify.py                   # Validation and utility functions (updated)
├── gemini_card_detector.py    # Gemini API integration module (NEW)
├── requirements.txt            # Python dependencies (updated with google-generativeai)
├── GEMINI_USAGE.py            # Quick reference and examples
├── ID_Verification.ipynb      # Jupyter notebook demo
├── submissions.csv            # Saved submissions (created at runtime)
└── README.md                  # This file
```

## Available Functions

### From `gemini_card_detector.py`

#### `configure_gemini(api_key: str) -> bool`
Configure Gemini API with your key.

#### `detect_card_type(pil_img: Image, api_key: str) -> Tuple[str, float]`
Detect the type of ID card. Returns (card_type, confidence).
- **Returns**: Tuple of (card_type, confidence_score)
- **card_type**: One of 'Ghana Card', 'Voter ID Card', 'Ghana Passport', 'Ghana Driver\'s License', 'Other'

#### `extract_card_text(pil_img: Image, card_type: str = None, api_key: str = None) -> Dict`
Extract labeled text fields from the card.
- **Returns**: Dictionary with:
  - `text_fields`: Extracted key-value pairs
  - `raw_ocr`: Full text from card
  - `confidence`: Extraction confidence (0-1)
  - `success`: Boolean success flag
  - `message`: Status message

#### `analyze_card_complete(pil_img: Image, api_key: str) -> Dict`
Complete analysis: detect type and extract text in one call.
- **Returns**: Comprehensive analysis result with both detection and extraction

### From `verify.py`

#### `analyze_card_gemini(pil_img, api_key) -> Dict`
Wrapper for complete Gemini analysis.

#### `detect_card_type_gemini(pil_img, api_key) -> Tuple[str, float]`
Wrapper for card type detection.

#### `extract_card_text_gemini(pil_img, card_type=None, api_key=None) -> Dict`
Wrapper for text extraction.

## Expected Output Examples

### Ghana Card
```json
{
  "text_fields": {
    "name": "John Kwame Doe",
    "date_of_birth": "1990-05-15",
    "id_number": "GHA-123456789-0",
    "sex": "M",
    "nationality": "Ghanaian",
    "issuing_authority": "National Identification Authority",
    "expiry_date": "2030-05-15"
  },
  "raw_ocr": "REPUBLIC OF GHANA...",
  "confidence": 0.92
}
```

### Voter ID Card
```json
{
  "text_fields": {
    "surname": "Doe",
    "firstname": "John",
    "date_of_birth": "1990-05-15",
    "voter_id": "1234567890",
    "registration_date": "2020-08-12",
    "constituency": "Accra Central"
  },
  "raw_ocr": "VOTER IDENTIFICATION CARD...",
  "confidence": 0.88
}
```

## Supported Card Types

| Card Type | Detection | Text Extraction | Notes |
|-----------|-----------|-----------------|-------|
| Ghana Card | ✅ | ✅ | Official national ID |
| Voter ID | ✅ | ✅ | Electoral Commission ID |
| Ghana Passport | ✅ | ✅ | Travel document |
| Driver's License | ✅ | ✅ | DVLA issued license |
| Other | ✅ | ✅ | For non-Ghana IDs |

## How It Works

### Card Type Detection Flow
1. Image is sent to Gemini Vision API
2. API analyzes card appearance, colors, logos, text patterns
3. Returns detected type with confidence score (0-1)
4. Validates against known card types

### Text Extraction Flow
1. Card image sent to Gemini Vision
2. API identifies all visible labels on card
3. Extracts corresponding values for each label
4. Returns structured JSON with field-value pairs
5. Also returns full OCR text and confidence

### Validation Flow
1. Uses extracted fields + manual entry
2. Applies regex validation rules per card type
3. Checks OCR text for key markers
4. Returns pass/fail for each field
5. Generates overall validation score

## Error Handling

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| "Failed to configure Gemini API" | Invalid API key | Check key at https://aistudio.google.com/app/apikeys |
| Low confidence scores | Poor image quality | Ensure clear, well-lit, straight card image |
| Missing fields in extraction | Blurry text or image angle | Retake photo with better lighting and positioning |
| "Gemini not available" | Package not installed | Run `pip install google-generativeai` |

## Data Privacy & Security

- **API Key**: Keep your API key private; never commit to version control
- **Image Storage**: Images are sent to Google's Gemini API during analysis
- **Local Storage**: Submissions saved to `submissions.csv` locally
- **HTTPS**: All API calls use encrypted HTTPS
- **No Cache**: Images not cached or stored by the application

## Performance Notes

- First call may take 2-3 seconds (API latency)
- Subsequent calls typically 1-2 seconds
- Image preprocessing adds minimal overhead
- Works with JPG, PNG formats
- Optimal card image: 1024x768 or higher

## Requirements

See `requirements.txt` for full list. Key packages:

- `google-generativeai` - Gemini API client
- `pillow` - Image processing
- `streamlit` - Web interface
- `pandas` - Data handling
- `opencv-python` (optional) - Advanced image processing
- `face_recognition` (optional) - Face matching

## Tips for Best Results

✅ **Card Image Quality**
- Ensure good lighting (no shadows)
- Card should be straight and in frame
- Entire card visible, no cropping
- High resolution (1024+ pixels)
- Focus on text clarity

✅ **Portrait Quality**
- Clear, well-lit face photo
- Professional passport-style photo
- Face taking up 70-80% of image
- Neutral background preferred

✅ **Card Positioning**
- Lay card flat on white/neutral background
- Take photo from directly above
- Avoid reflections and glare
- Ensure all text is readable

## Troubleshooting

### App won't start
```powershell
# Check Python version (3.8+)
python --version

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Clear cache
rm -r __pycache__
```

### Low confidence in card detection
- This is normal; confidence < 0.7 still provides useful hints
- System will still extract text even with low confidence
- User can manually confirm/override

### Memory issues with large images
- App auto-converts to JPEG
- Maximum practical image size: 5MB
- Larger images automatically downscaled

## Support

For issues or questions:
1. Check GEMINI_USAGE.py for examples
2. Review error messages in console
3. Ensure API key is valid
4. Verify image quality and format

## License

This project is for educational and internal use.

## Contact

For issues or feature requests, contact the development team.

---

**Last Updated**: December 2024
**Version**: 1.0 with Gemini API Integration

