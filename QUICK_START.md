# 🚀 Quick Start Guide - Gemini ID Verification

## ⚡ 5-Minute Setup

### Step 1: Get API Key (1 minute)
1. Go to https://aistudio.google.com/app/apikeys
2. Click **"Create API Key"**
3. Copy the key (looks like: `AIzaSy...`)

### Step 2: Install Dependencies (2 minutes)
```powershell
# Navigate to project
cd C:\Users\ABY\Desktop\ML

# Create/activate environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt
```

### Step 3: Run the App (instant)
```powershell
python -m streamlit run app_gemini.py
```

The app opens in your browser. Paste your API key in the sidebar and you're ready!

---

## 📋 What the System Does

### Task 1: Card Type Detection ✓
- Analyzes card image
- Identifies: Ghana Card, Voter ID, Passport, Driver's License, or Other
- Returns confidence score (0-100%)

### Task 2: Text Extraction ✓
- Reads all visible labels on card (Name, Date of Birth, ID Number, etc.)
- Extracts corresponding values
- Returns structured JSON with field-value pairs

### Task 3: Structured Output ✓
- All results in single JSON object
- Includes metadata (confidence, success status, notes)
- Ready for database storage or API integration

---

## 🎯 Usage Examples

### Using the Web App (Easiest)
```
1. Upload portrait photo
2. Upload ID card image
3. App automatically detects type & extracts text
4. Review results
5. Click "Save Submission"
```

### Using Python Script
```python
from PIL import Image
from verify import analyze_card_gemini

api_key = "<GEMINI_API_KEY>"
card_img = Image.open("ghana_card.jpg")

result = analyze_card_gemini(card_img, api_key)

print("Card Type:", result['card_type'])
print("Fields:", result['text_extraction']['text_fields'])
```

---

## 📁 Files Created/Modified

### New Files:
- `gemini_card_detector.py` - Core Gemini integration
- `app_gemini.py` - Web interface with Gemini
- `GEMINI_README.md` - Full documentation
- `GEMINI_USAGE.py` - Code examples
- `test_setup.py` - Verification script

### Modified Files:
- `requirements.txt` - Added google-generativeai
- `verify.py` - Added Gemini wrapper functions

---

## ✅ Verify Installation

```powershell
python test_setup.py
```

This checks:
- All packages installed ✓
- All modules working ✓
- API key valid ✓
- Gemini API responding ✓

---

## 📊 Expected Output

```json
{
  "card_type": "Ghana Card",
  "card_type_confidence": 0.95,
  "text_extraction": {
    "success": true,
    "text_fields": {
      "name": "John Doe",
      "date_of_birth": "1990-05-15",
      "id_number": "GHA-123456789-0",
      "nationality": "Ghanaian",
      "expiry_date": "2030-05-15"
    },
    "raw_ocr": "REPUBLIC OF GHANA...",
    "confidence": 0.92
  }
}
```

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "API key invalid" | Go to https://aistudio.google.com/app/apikeys and create new key |
| "Module not found" | Run `pip install -r requirements.txt` |
| "Low confidence" | Take clearer photo of card (better lighting, straight angle) |
| "Blank extraction" | Ensure card text is clearly visible in image |

---

## 🔒 Security Notes

- ✓ Keep API key private (don't share or commit to git)
- ✓ Images deleted after processing
- ✓ HTTPS encryption for all API calls
- ✓ No image storage or caching

---

## 🎓 Next Steps

1. ✓ **Run the app**: `streamlit run app_gemini.py`
2. ✓ **Test with sample**: Upload a card image
3. ✓ **Check results**: Review extracted fields
4. ✓ **Integrate**: Use `analyze_card_gemini()` in your code
5. ✓ **Scale**: Deploy to production when ready

---

## 📖 Full Documentation

See `GEMINI_README.md` for:
- Detailed API documentation
- All available functions
- Advanced usage examples
- Supported card types
- Error handling

---

## 🎯 Tasks Completed

✅ **Task 1: Card Type Detection**
- Using Gemini Vision API
- Supports Ghana Card, Voter ID, Passport, Driver's License
- Returns type + confidence score

✅ **Task 2: Text Extraction (OCR)**
- Based on labels found on card
- Extracts field-value pairs automatically
- Returns structured JSON

✅ **Task 3: Structured Output**
- Single JSON object with all findings
- Includes metadata (confidence, success status)
- Ready for integration with any system

---

## 💡 Pro Tips

1. **Better accuracy**: Use high-quality, well-lit card images
2. **Batch processing**: Use `analyze_card_gemini()` in loops for multiple cards
3. **Error handling**: Check `success` field before processing results
4. **Confidence threshold**: Only process if `card_type_confidence > 0.7`
5. **Fallback**: Manual fields available if auto-detection fails

---

**You're all set!** 🎉

Start the app: `python -m streamlit run app_gemini.py`

