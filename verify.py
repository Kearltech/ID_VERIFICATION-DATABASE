from PIL import Image
import io
import re
import numpy as np
import pandas as pd

# Optional imports guarded
try:
    import pytesseract
    _have_pytesseract = True
except Exception:
    pytesseract = None
    _have_pytesseract = False

try:
    import face_recognition
    _have_face_recognition = True
except Exception:
    face_recognition = None
    _have_face_recognition = False


def pil_from_upload(uploaded_file):
    """Return a PIL.Image from a Streamlit/Python uploaded file-like object."""
    if uploaded_file is None:
        return None
    if hasattr(uploaded_file, 'read'):
        data = uploaded_file.read()
    else:
        data = uploaded_file
    try:
        img = Image.open(io.BytesIO(data)).convert('RGB')
        return img
    except Exception:
        return None


def ocr_text_from_image(pil_img):
    """Extract OCR text using pytesseract if available. Returns tuple (text, confidence_flag)."""
    if pil_img is None:
        return "", 0.0
    if not _have_pytesseract:
        return "", 0.0
    try:
        text = pytesseract.image_to_string(pil_img)
        # Confidence estimate is not precise here; return 0.0 to 1.0 placeholder
        return text, 0.8
    except Exception:
        return "", 0.0


def detect_faces(pil_img):
    """Return list of face locations (top,right,bottom,left) using face_recognition if available."""
    if pil_img is None or not _have_face_recognition:
        return []
    arr = np.array(pil_img)
    try:
        locs = face_recognition.face_locations(arr)
        return locs
    except Exception:
        return []


def face_match(pil_img1, pil_img2, tolerance=0.6):
    """Compare two PIL images and return (match_boolean, distance) or (None, None) if unsupported."""
    if pil_img1 is None or pil_img2 is None or not _have_face_recognition:
        return None, None
    try:
        arr1 = np.array(pil_img1)
        arr2 = np.array(pil_img2)
        enc1 = face_recognition.face_encodings(arr1)
        enc2 = face_recognition.face_encodings(arr2)
        if len(enc1) == 0 or len(enc2) == 0:
            return False, None
        dists = face_recognition.face_distance(enc1, enc2[0])
        best = float(np.min(dists))
        match = bool(best <= tolerance)
        return match, best
    except Exception:
        return False, None


# Validation helpers

def validate_ghana_pin(pin):
    # Expected format: GHA-000000000-0 (example)
    if not isinstance(pin, str):
        return False
    return bool(re.match(r"^GHA-\d{9}-\d$", pin.strip()))


def validate_voter_id(voter_id):
    # 10 digits
    if not isinstance(voter_id, str):
        return False
    return bool(re.match(r"^\d{10}$", voter_id.strip()))


def validate_drivers_license_number(num):
    # Basic check: alphanumeric and length 5-20
    if not isinstance(num, str):
        return False
    return bool(re.match(r"^[A-Za-z0-9\-/ ]{5,20}$", num.strip()))


def validate_passport_number(num):
    # Alphanumeric short string
    if not isinstance(num, str):
        return False
    return bool(re.match(r"^[A-Za-z0-9]{5,25}$", num.strip()))


def validate_fields(id_type, entered, ocr_text_raw):
    """Validate a set of entered fields against id_type and any OCR text.

    entered: dict with keys like id_number, surname, firstname, dob, sex, etc.
    ocr_text_raw: text string from OCR of card (may be empty)
    Returns: dict of field -> {pass:bool, msg:str}
    """
    o = {}
    ocr = (ocr_text_raw or "").upper()
    id_type = (id_type or "").lower()

    # Common checks
    idnum = entered.get('id_number', '')
    dob = entered.get('date_of_birth', '')

    if 'ghana' in id_type:
        o['id_number'] = {'pass': validate_ghana_pin(idnum), 'msg': 'Ghana PIN format GHA-000000000-0 expected'}
        # presence of republic text
        o['republic_text'] = {'pass': 'REPUBLIC OF GHANA' in ocr, 'msg': "Contains 'REPUBLIC OF GHANA'"}
        # Name fields
        o['surname'] = {'pass': bool(entered.get('surname')), 'msg': 'Surname provided'}
        o['dob'] = {'pass': bool(dob), 'msg': 'DOB provided'}
    elif 'driver' in id_type:
        o['id_number'] = {'pass': validate_drivers_license_number(idnum), 'msg': 'Driver license number format seems invalid'}
        o['dob'] = {'pass': bool(dob), 'msg': 'DOB provided'}
        o['nationality'] = {'pass': bool(entered.get('nationality')), 'msg': 'Nationality provided'}
    elif 'voter' in id_type:
        o['id_number'] = {'pass': validate_voter_id(idnum), 'msg': 'Voter ID must be 10 digits'}
        o['surname'] = {'pass': bool(entered.get('surname')), 'msg': 'Surname provided'}
        o['registration_date'] = {'pass': bool(entered.get('registration_date')), 'msg': 'Registration date provided'}
        o['barcode'] = {'pass': 'BARCODE' in ocr or 'VOTER' in ocr, 'msg': 'Barcode or voter text present in OCR'}
    elif 'passport' in id_type:
        o['id_number'] = {'pass': validate_passport_number(idnum), 'msg': 'Passport number format looks wrong'}
        o['issuing_state'] = {'pass': bool(entered.get('issuing_state')), 'msg': 'Issuing state provided'}
        o['republic_passport'] = {'pass': 'PASSPORT' in ocr or 'REPUBLIC' in ocr, 'msg': "Contains 'PASSPORT' or 'REPUBLIC'"}
    else:
        o['id_number'] = {'pass': bool(idnum), 'msg': 'ID number provided'}

    # Overall simple summary
    all_pass = all(v['pass'] for v in o.values()) if o else False
    return {'fields': o, 'overall': all_pass}


def save_submission(record, csv_path='submissions.csv'):
    """Append a record (dict) to CSV using pandas."""
    try:
        df = pd.DataFrame([record])
        # if file exists, append without header
        from pathlib import Path
        p = Path(csv_path)
        if p.exists():
            df.to_csv(csv_path, mode='a', header=False, index=False)
        else:
            df.to_csv(csv_path, index=False)
        return True
    except Exception:
        return False
