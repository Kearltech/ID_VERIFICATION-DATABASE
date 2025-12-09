from PIL import Image
import io
import re
import numpy as np
import pandas as pd

# Phase 2 Integration
from logger_config import audit_logger
from validators import InputValidator
from exceptions import create_error, TextExtractionError, ValidationError

# Phase 3 Integration - OCR Comparison
from ocr_comparison import compare_user_input_with_ocr

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

# OpenCV face detection as fallback
try:
    import cv2
    _have_opencv = True
except Exception:
    cv2 = None
    _have_opencv = False

# Enhanced face comparison module
try:
    from face_comparison import compare_passport_to_id, get_face_comparator
    _have_face_comparison = True
except Exception:
    _have_face_comparison = False

try:
    from gemini_card_detector import (
        detect_card_type, 
        extract_card_text, 
        analyze_card_complete,
        configure_gemini
    )
    _have_gemini = True
except Exception:
    _have_gemini = False


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
        audit_logger.logger.warning('OCR attempted on None image', extra={'event': 'ocr_invalid_input'})
        return "", 0.0
    if not _have_pytesseract:
        audit_logger.logger.warning('pytesseract not available', extra={'event': 'ocr_pytesseract_unavailable'})
        return "", 0.0
    try:
        text = pytesseract.image_to_string(pil_img)
        audit_logger.logger.info('OCR extraction successful', extra={
            'event': 'ocr_success',
            'text_length': len(text) if text else 0,
            'confidence': 0.8
        })
        # Confidence estimate is not precise here; return 0.0 to 1.0 placeholder
        return text, 0.8
    except Exception as e:
        audit_logger.logger.error(f'OCR extraction failed: {str(e)}', extra={'event': 'ocr_error', 'error': str(e)})
        return "", 0.0


def detect_faces(pil_img):
    """Return list of face locations (top,right,bottom,left) using face_recognition if available."""
    if pil_img is None or not _have_face_recognition:
        audit_logger.logger.warning('Face detection unavailable', extra={
            'event': 'face_detection_unavailable',
            'has_image': pil_img is not None,
            'has_library': _have_face_recognition
        })
        return []
    
    try:
        # Ensure image is in RGB format for face_recognition
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        
        arr = np.array(pil_img)
        
        # Use 'hog' model first (faster, good for portraits), fallback to 'cnn' if needed
        try:
            locs = face_recognition.face_locations(arr, model='hog')
            if not locs:  # If HOG fails, try CNN
                locs = face_recognition.face_locations(arr, model='cnn')
        except Exception:
            # Fallback to default (hog) if model specification fails
            locs = face_recognition.face_locations(arr)
        
        audit_logger.logger.info('Face detection completed', extra={
            'event': 'face_detection_success',
            'faces_count': len(locs),
            'image_shape': arr.shape
        })
        return locs
    except Exception as e:
        audit_logger.logger.error(f'Face detection failed: {str(e)}', extra={'event': 'face_detection_error', 'error': str(e)})
        return []


def face_match(pil_img1, pil_img2, tolerance=0.6):
    """Compare two PIL images and return (match_boolean, distance) or (None, None) if unsupported.
    
    Uses enhanced face comparison module with multiple methods if available,
    falls back to OpenCV-only implementation.
    """
    if pil_img1 is None or pil_img2 is None:
        audit_logger.logger.warning('Face matching unavailable - missing image', extra={
            'event': 'face_match_unavailable',
            'has_img1': pil_img1 is not None,
            'has_img2': pil_img2 is not None
        })
        return None, None
    
    # Try enhanced face comparison module first (best accuracy)
    if _have_face_comparison:
        try:
            match, score, details = compare_passport_to_id(pil_img1, pil_img2, method='ensemble')
            if match is not None:
                # Convert similarity score to distance (inverse)
                distance = 1.0 - score
                audit_logger.logger.info('Face matching completed (enhanced)', extra={
                    'event': 'face_match_success_enhanced',
                    'match': match,
                    'similarity': score,
                    'distance': distance,
                    'methods': list(details.keys())
                })
                return match, distance
        except Exception as e:
            audit_logger.logger.debug(f'Enhanced face comparison failed, trying fallback: {e}')
    
    # Try face_recognition library
    if _have_face_recognition:
        try:
            arr1 = np.array(pil_img1)
            arr2 = np.array(pil_img2)
            enc1 = face_recognition.face_encodings(arr1)
            enc2 = face_recognition.face_encodings(arr2)
            if len(enc1) == 0 or len(enc2) == 0:
                audit_logger.logger.warning('No faces found in one or both images (face_recognition)', extra={
                    'event': 'face_match_no_faces',
                    'faces_img1': len(enc1),
                    'faces_img2': len(enc2)
                })
                # Fall through to OpenCV fallback
            else:
                dists = face_recognition.face_distance(enc1, enc2[0])
                best = float(np.min(dists))
                match = bool(best <= tolerance)
                audit_logger.logger.info('Face matching completed (face_recognition)', extra={
                    'event': 'face_match_success',
                    'match': match,
                    'distance': best,
                    'tolerance': tolerance
                })
                return match, best
        except Exception as e:
            audit_logger.logger.debug(f'face_recognition failed, trying OpenCV: {e}')
    
    # Fallback to OpenCV haar cascade
    if _have_opencv:
        try:
            # Convert PIL images to OpenCV format
            arr1 = cv2.cvtColor(np.array(pil_img1), cv2.COLOR_RGB2BGR)
            arr2 = cv2.cvtColor(np.array(pil_img2), cv2.COLOR_RGB2BGR)
            
            # Load haar cascade for face detection
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            # Detect faces
            faces1 = face_cascade.detectMultiScale(cv2.cvtColor(arr1, cv2.COLOR_BGR2GRAY), 1.3, 5)
            faces2 = face_cascade.detectMultiScale(cv2.cvtColor(arr2, cv2.COLOR_BGR2GRAY), 1.3, 5)
            
            if len(faces1) == 0 or len(faces2) == 0:
                audit_logger.logger.warning('No faces found in one or both images (OpenCV)', extra={
                    'event': 'face_match_no_faces_opencv',
                    'faces_img1': len(faces1),
                    'faces_img2': len(faces2)
                })
                return None, None
            
            # Extract face regions and compare
            x1, y1, w1, h1 = faces1[0]
            x2, y2, w2, h2 = faces2[0]
            
            face_img1 = arr1[y1:y1+h1, x1:x1+w1]
            face_img2 = arr2[y2:y2+h2, x2:x2+w2]
            
            # Resize to same size for comparison
            face_img1 = cv2.resize(face_img1, (100, 100))
            face_img2 = cv2.resize(face_img2, (100, 100))
            
            # Compute structural similarity (simple approach)
            # Using histogram comparison as a proxy for face similarity
            hist1 = cv2.calcHist([face_img1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            hist2 = cv2.calcHist([face_img2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            
            # Normalize histograms
            hist1 = cv2.normalize(hist1, hist1).flatten()
            hist2 = cv2.normalize(hist2, hist2).flatten()
            
            # Compare using different methods
            # Bhattacharyya distance (0 = identical, 1 = completely different)
            distance = cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)
            
            # Convert to match score (inverse of distance, with threshold)
            match_threshold = 0.3  # Lower distance means better match
            match = bool(distance < match_threshold)
            
            audit_logger.logger.info('Face matching completed (OpenCV)', extra={
                'event': 'face_match_success_opencv',
                'match': match,
                'distance': distance,
                'threshold': match_threshold
            })
            
            return match, distance
            
        except Exception as e:
            audit_logger.logger.error(f'OpenCV face matching failed: {str(e)}', extra={
                'event': 'face_match_error_opencv',
                'error': str(e)
            })
            return None, None
    
    # No face matching available
    audit_logger.logger.warning('Face matching unavailable - no suitable library', extra={
        'event': 'face_match_unavailable_no_library',
        'has_face_recognition': _have_face_recognition,
        'has_opencv': _have_opencv
    })
    return None, None


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
    validator = InputValidator()
    o = {}
    ocr = (ocr_text_raw or "").upper()
    id_type = (id_type or "").lower()

    # Common checks
    idnum = entered.get('id_number', '')
    dob = entered.get('date_of_birth', '')

    audit_logger.logger.info('Field validation started', extra={
        'event': 'validation_start',
        'id_type': id_type,
        'fields_count': len(entered)
    })

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
    
    audit_logger.logger.info('Field validation completed', extra={
        'event': 'validation_complete',
        'id_type': id_type,
        'passed': all_pass,
        'fields_validated': len(o)
    })
    
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
        
        audit_logger.logger.info('Submission saved to CSV', extra={
            'event': 'submission_saved',
            'csv_path': csv_path,
            'id_type': record.get('id_type'),
            'validation_passed': record.get('validation_overall')
        })
        return True
    except Exception as e:
        audit_logger.logger.error(f'Failed to save submission: {str(e)}', extra={
            'event': 'submission_save_failed',
            'error': str(e),
            'csv_path': csv_path
        })
        return False


# Gemini API-based functions

def detect_card_type_gemini(pil_img, api_key):
    """
    Detect card type using Gemini API.
    Returns tuple: (card_type, confidence)
    """
    if not _have_gemini or pil_img is None:
        return 'Other', 0.0
    try:
        return detect_card_type(pil_img, api_key=api_key)
    except Exception as e:
        print(f"Error in detect_card_type_gemini: {e}")
        return 'Other', 0.0


def extract_card_text_gemini(pil_img, card_type=None, api_key=None):
    """
    Extract text from card using Gemini Vision API.
    Returns dict with text_fields, raw_ocr, confidence, success, and message.
    """
    if not _have_gemini or pil_img is None:
        return {
            "text_fields": {},
            "raw_ocr": "",
            "confidence": 0.0,
            "success": False,
            "message": "Gemini not available"
        }
    try:
        return extract_card_text(pil_img, card_type=card_type, api_key=api_key)
    except Exception as e:
        print(f"Error in extract_card_text_gemini: {e}")
        return {
            "text_fields": {},
            "raw_ocr": "",
            "confidence": 0.0,
            "success": False,
            "message": str(e)
        }


def analyze_card_gemini(pil_img, api_key):
    """
    Complete card analysis using Gemini: detect type and extract text.
    Returns dict with card_type, text_extraction, and analysis metadata.
    """
    if not _have_gemini or pil_img is None:
        return {
            "card_type": "Other",
            "card_type_confidence": 0.0,
            "text_extraction": {
                "text_fields": {},
                "raw_ocr": "",
                "confidence": 0.0,
                "success": False
            },
            "success": False,
            "message": "Gemini not available"
        }
    try:
        return analyze_card_complete(pil_img, api_key)
    except Exception as e:
        print(f"Error in analyze_card_gemini: {e}")
        return {
            "card_type": "Other",
            "card_type_confidence": 0.0,
            "text_extraction": {
                "text_fields": {},
                "raw_ocr": "",
                "confidence": 0.0,
                "success": False
            },
            "success": False,
            "message": str(e)
        }


def compare_ocr_with_user_input(id_type, user_data, ocr_data):
    """
    Compare OCR-extracted data with user-entered data using intelligent field-level comparison.
    
    Args:
        id_type: Type of ID document (e.g., 'Ghana Card', 'Voter ID')
        user_data: Dictionary of user-entered field values
        ocr_data: Dictionary of OCR-extracted field values
    
    Returns:
        Dictionary with comparison results including:
            - valid: bool - True if comparison passed overall
            - passed_fields: list - Fields that matched
            - failed_fields: list - Fields that didn't match
            - missing_fields: list - Fields with missing values
            - details: dict - Detailed comparison for each field
            - message: str - Human-readable summary
    """
    try:
        audit_logger.logger.info('Starting OCR vs user input comparison', extra={
            'event': 'ocr_comparison_init',
            'id_type': id_type
        })
        
        # Use phase 3 OCR comparison module
        result = compare_user_input_with_ocr(id_type, user_data, ocr_data)
        summary = result.get_summary()
        
        # Log detailed results
        audit_logger.logger.info('OCR comparison completed', extra={
            'event': 'ocr_comparison_result',
            'id_type': id_type,
            'valid': result.is_valid(),
            'passed_count': summary['passed_count'],
            'failed_count': summary['failed_count'],
            'missing_count': summary['missing_count']
        })
        
        # Build response
        response = {
            'valid': result.is_valid(),
            'passed_fields': result.passed_fields,
            'failed_fields': result.failed_fields,
            'missing_fields': result.missing_fields,
            'details': summary['comparisons'],
            'message': f"Comparison complete: {summary['passed_count']} passed, "
                      f"{summary['failed_count']} failed, {summary['missing_count']} missing"
        }
        
        # Log field-level details if there are failures
        if result.failed_fields:
            for field in result.failed_fields:
                comp = summary['comparisons'].get(field, {})
                audit_logger.logger.warning('Field mismatch detected', extra={
                    'event': 'field_mismatch',
                    'field': field,
                    'type': comp.get('type', 'unknown'),
                    'message': comp.get('message', '')
                })
        
        return response
    
    except Exception as e:
        audit_logger.logger.error('OCR comparison error', extra={
            'event': 'ocr_comparison_error',
            'error': str(e)
        })
        
        return {
            'valid': False,
            'passed_fields': [],
            'failed_fields': [],
            'missing_fields': [],
            'details': {},
            'message': f"Comparison error: {str(e)}"
        }


