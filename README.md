# ID Verification Project

This project provides a simple demo for verifying uploaded portraits and ID cards.

Structure

- `.venv/` — virtual environment (created locally)
- `ID_Verification.ipynb` — Notebook demo / tests
- `app.py` — Streamlit app for interactive verification
- `verify.py` — helper functions (OCR, face detection, validation rules)
- `requirements.txt` — project dependencies (regenerate with `pip freeze`)
- `submissions.csv` — saved submissions (created at runtime)

Quick start (Windows PowerShell)

```powershell
# Create venv
python -m venv .venv

# Activate
.venv\Scripts\Activate.ps1  # or .venv\Scripts\activate for cmd.exe

# Upgrade pip and install
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install streamlit pillow pandas numpy
# Optional for OCR / face match
.venv\Scripts\python -m pip install pytesseract face_recognition opencv-python

# Regenerate requirements
.venv\Scripts\python -m pip freeze > requirements.txt

# Run notebook (from activated venv)
# jupyter notebook

# Run Streamlit app
.venv\Scripts\python -m streamlit run app.py
```

Notes

- `pytesseract` requires the Tesseract binary installed on your machine and in PATH.
- `face_recognition` requires dlib and can be tricky to install on Windows; use the optional features only if you can install the dependencies.
- The app saves submissions to `submissions.csv` in the project root.

