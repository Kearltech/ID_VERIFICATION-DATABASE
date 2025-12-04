# Configuration and Environment Setup Guide

## 🔑 API Key Management

### Getting Your Gemini API Key

1. Visit: https://aistudio.google.com/app/apikeys
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Select or create a Google Cloud project
5. Copy the generated API key

### Storing the API Key Securely

**Option 1: Environment Variable (Recommended)**
```powershell
# Set temporarily in PowerShell
$env:GEMINI_API_KEY = "<GEMINI_API_KEY>"

# Verify it's set
$env:GEMINI_API_KEY
```

**Option 2: .env File**
```bash
# Create .env file in project root
GEMINI_API_KEY=<GEMINI_API_KEY>

# Then load it in your code:
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
```

**Option 3: Streamlit Secrets (For Production)**
```
# ~/.streamlit/secrets.toml
gemini_api_key = "<GEMINI_API_KEY>"

# In app code:
import streamlit as st
api_key = st.secrets["gemini_api_key"]
```

---

## 🔧 Environment Configuration

### Python Virtual Environment

**Create**:
```powershell
python -m venv .venv
```

**Activate (PowerShell)**:
```powershell
.venv\Scripts\Activate.ps1
```

**Activate (CMD)**:
```cmd
.venv\Scripts\activate.bat
```

**Deactivate**:
```powershell
deactivate
```

### Dependency Installation

**Install all**:
```powershell
pip install -r requirements.txt
```

**Install specific package**:
```powershell
pip install google-generativeai==0.8.3
```

**Update specific package**:
```powershell
pip install --upgrade google-generativeai
```

**Check installed packages**:
```powershell
pip list
```

---

## 🎛️ Streamlit Configuration

### Streamlit Config File

Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[client]
showErrorDetails = true
toolbarMode = "viewer"

[logger]
level = "info"

[server]
port = 8501
headless = false
```

### Streamlit Secrets

Create `.streamlit/secrets.toml`:
```toml
gemini_api_key = "<GEMINI_API_KEY>"
```

---

## 🚀 Running the Application

### Development Mode

```powershell
# Activate environment
.venv\Scripts\Activate.ps1

# Run Streamlit in development
python -m streamlit run app_gemini.py --logger.level=debug

# Run with custom port
python -m streamlit run app_gemini.py --server.port 8502
```

### Production Mode

```powershell
# Run without logger.level=debug
python -m streamlit run app_gemini.py

# Run with headless (for servers)
python -m streamlit run app_gemini.py --logger.level=error --client.showErrorDetails=false
```

---

## 🐍 Python Version Requirements

**Minimum**: Python 3.8  
**Recommended**: Python 3.11+  
**Tested With**: Python 3.10, 3.11, 3.12

**Check your Python version**:
```powershell
python --version
```

**Upgrade pip**:
```powershell
python -m pip install --upgrade pip
```

---

## 🔍 Gemini API Configuration

### API Rate Limits

- **Free tier**: 15 requests per minute
- **Paid tier**: Varies by plan
- **Check quotas**: https://aistudio.google.com/app/apikeys

### Model Selection

Current implementation uses: `gemini-1.5-flash`

Available models:
- `gemini-1.5-flash` - Fast, cheap (current)
- `gemini-1.5-pro` - Slower, more accurate
- `gemini-2.0-flash` - Latest fast model

To change model, edit `gemini_card_detector.py`:
```python
model = genai.GenerativeModel('gemini-1.5-pro')  # Change here
```

---

## 🖼️ Image Processing Settings

### Supported Formats
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)

### Image Size Guidelines
- **Minimum**: 256x256 pixels
- **Recommended**: 1024x768 pixels or larger
- **Maximum**: 5MB (auto-compressed by app)

### Image Quality Tips
1. Use high resolution (1080p+)
2. Ensure good lighting (no harsh shadows)
3. Card should be straight and flat
4. No reflections or glare
5. Entire card visible in frame

---

## 💾 Database Configuration

### CSV Storage

Submissions are saved to `submissions.csv` with fields:
- id_type
- id_number
- surname
- firstname
- date_of_birth
- validation_overall
- face_match
- gemini_card_type
- gemini_confidence

### Backing Up Data

```powershell
# Copy submissions to backup
Copy-Item submissions.csv submissions_backup_$(Get-Date -f 'yyyyMMdd_HHmmss').csv

# Archive old submissions
if (Test-Path submissions.csv) {
    Move-Item submissions.csv submissions_$(Get-Date -f 'yyyyMMdd').csv
}
```

---

## 🧪 Testing Configuration

### Run Tests

```powershell
# Full setup verification
python test_setup.py

# Run specific tests
pytest -v test_setup.py

# With coverage
pytest --cov=gemini_card_detector test_setup.py
```

### Debug Mode

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in Streamlit:
st.set_page_config(
    page_title='App',
    initial_sidebar_state="expanded",
    layout="wide"
)

# Then check browser console for debug info
```

---

## 📊 Monitoring and Logging

### Streamlit Logs

Logs appear in terminal running Streamlit:
```
2024-12-04 10:30:45 - INFO - Session started
2024-12-04 10:30:46 - DEBUG - Image loaded: 1024x768
2024-12-04 10:30:50 - INFO - Gemini API called
```

### Application Logs

```python
# In your code:
import logging

logger = logging.getLogger(__name__)
logger.info("Starting analysis")
logger.warning("Low confidence detected")
logger.error("API error occurred")
```

### Monitoring Gemini API

Check your quota at:
- https://aistudio.google.com/app/apikeys
- Google Cloud Console: console.cloud.google.com

---

## 🔒 Security Checklist

- [ ] API key stored safely (not in code)
- [ ] .env file added to .gitignore
- [ ] No secrets in version control
- [ ] HTTPS enforced for all connections
- [ ] Input validation enabled
- [ ] Error messages don't expose sensitive info
- [ ] Images deleted after processing
- [ ] Submissions CSV has appropriate permissions

### .gitignore Setup

```
# .gitignore
.env
.streamlit/secrets.toml
submissions.csv
__pycache__/
*.pyc
.venv/
*.log
*.tmp
```

---

## 🚨 Troubleshooting Configuration Issues

### Issue: Module not found
```powershell
# Reinstall all dependencies
pip install --force-reinstall -r requirements.txt
```

### Issue: API key not recognized
```powershell
# Verify API key format
$env:GEMINI_API_KEY | Write-Host

# Test connectivity
python -c "import google.generativeai; google.generativeai.configure(api_key='YOUR_KEY')"
```

### Issue: Streamlit cache issues
```powershell
# Clear Streamlit cache
streamlit cache clear

# Or delete cache directory
Remove-Item -Recurse ~/.streamlit/cache
```

### Issue: Port already in use
```powershell
# Use different port
python -m streamlit run app_gemini.py --server.port 8502

# Or find and kill process on port
Get-NetTCPConnection -LocalPort 8501 | Stop-Process -Force
```

---

## 📈 Performance Tuning

### Optimize Image Processing

```python
# In gemini_card_detector.py
# Reduce image size before sending to API
from PIL import Image

def resize_image(img, max_size=1024):
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    return img
```

### Cache API Responses

```python
import streamlit as st

@st.cache_data
def get_card_analysis(image_hash):
    # Cache results to avoid duplicate API calls
    pass
```

### Batch Processing

```python
# For multiple cards
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    results = executor.map(analyze_card_gemini, card_images)
```

---

## 📚 Resources

- **Gemini API**: https://aistudio.google.com
- **Python Docs**: https://docs.python.org
- **Streamlit**: https://docs.streamlit.io
- **PIL/Pillow**: https://pillow.readthedocs.io

---

## 🎯 Quick Commands Reference

```powershell
# Setup
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run
python -m streamlit run app_gemini.py

# Test
python test_setup.py

# Verify
pip list | Select-String "google\|pillow\|streamlit"

# Clean
Remove-Item -Recurse __pycache__
streamlit cache clear
```

---

**Last Updated**: December 4, 2024

