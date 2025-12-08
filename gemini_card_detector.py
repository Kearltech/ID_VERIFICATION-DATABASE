"""
Gemini API-based card type detection and text extraction.
Identifies card types and extracts labeled text fields using Google's Generative AI.
"""

import json
import base64
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from PIL import Image
import io

# Phase 2 Integration
from logger_config import audit_logger
from retry_utils import retry_api_call
from rate_limiter import APIUsageTracker, QuotaEnforcer
from exceptions import create_error, CardDetectionError, TextExtractionError

try:
    import google.generativeai as genai
    _have_gemini = True
except ImportError:
    _have_gemini = False

# Initialize usage tracking
usage_tracker = APIUsageTracker()
quota_enforcer = QuotaEnforcer(usage_tracker)


@retry_api_call
def configure_gemini(api_key: str) -> bool:
    """Configure Gemini API with the provided API key. Returns True if successful."""
    if not _have_gemini:
        audit_logger.logger.error('Gemini library not available', extra={'event': 'gemini_config_failed', 'reason': 'library_missing'})
        return False
    try:
        genai.configure(api_key=api_key)
        audit_logger.logger.info('Gemini API configured successfully', extra={'event': 'gemini_configured'})
        return True
    except Exception as e:
        audit_logger.logger.error(f'Error configuring Gemini: {str(e)}', extra={'event': 'gemini_config_error', 'error': str(e)})
        return False


def pil_to_base64(pil_img: Image.Image) -> str:
    """Convert PIL Image to base64 string for Gemini API."""
    if pil_img is None:
        return ""
    try:
        buffered = io.BytesIO()
        # Convert to RGB if necessary
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        pil_img.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return img_base64
    except Exception as e:
        print(f"Error converting image to base64: {e}")
        return ""


@retry_api_call
def detect_card_type(pil_img: Image.Image, api_key: str = None) -> Tuple[str, float]:
    """
    Detect the type of identification card using Gemini Vision API.
    
    Args:
        pil_img: PIL Image object of the ID card
        api_key: Gemini API key (if not already configured)
    
    Returns:
        Tuple of (card_type, confidence) where card_type is one of:
        'Ghana Card', 'Voter ID Card', 'Ghana Passport', 'Ghana Driver\'s License', 'Other'
        confidence is a float between 0 and 1
    """
    if not _have_gemini or pil_img is None:
        audit_logger.logger.warning('Card type detection unavailable', extra={
            'event': 'card_type_detection_unavailable',
            'has_gemini': _have_gemini,
            'has_image': pil_img is not None
        })
        return 'Other', 0.0
    
    if api_key:
        if not configure_gemini(api_key):
            audit_logger.logger.error('Failed to configure Gemini in detect_card_type', extra={'event': 'card_type_config_failed'})
            return 'Other', 0.0
    
    try:
        # Convert image to base64
        img_base64 = pil_to_base64(pil_img)
        if not img_base64:
            audit_logger.logger.error('Failed to convert image to base64', extra={'event': 'card_type_image_convert_failed'})
            return 'Other', 0.0
        
        # Check quota before making API call
        allowed, quota_info = quota_enforcer.check_quota_before_call('default_user')
        if not allowed:
            audit_logger.logger.warning('API quota exceeded', extra={'event': 'quota_exceeded', 'quota_info': quota_info})
            raise create_error('API_LIMIT_EXCEEDED')
        
        # Initialize Gemini model - use proper model name
        model = None
        # Use available model variants (gemini-1.5-flash is not available, use newer versions)
        model_names = [
            'gemini-2.5-flash',      # Try the latest model first
            'gemini-2.0-flash',      # Fallback to 2.0 flash
            'gemini-2.5-pro',        # Fallback to pro version
            'gemini-pro'             # Fallback to basic model
        ]
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                audit_logger.logger.debug(f'Using model: {model_name}', extra={'event': 'model_selected', 'model': model_name})
                break
            except Exception as e:
                audit_logger.logger.debug(f'Model {model_name} not available: {e}')
                continue
        
        if model is None:
            audit_logger.logger.error('No suitable Gemini model available', extra={'event': 'no_model_available'})
            return 'Other', 0.0
        
        # Create prompt for card type detection
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
        
        # Call Gemini API with vision capabilities
        response = model.generate_content([
            prompt,
            {
                "mime_type": "image/jpeg",
                "data": img_base64
            }
        ])
        
        # Parse response
        response_text = response.text
        
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            card_type = result.get('card_type', 'Other')
            confidence = float(result.get('confidence', 0.0))
            
            # Validate card type
            valid_types = ['Ghana Card', 'Voter ID Card', 'Ghana Passport', 
                          'Ghana Driver\'s License', 'Other']
            if card_type not in valid_types:
                card_type = 'Other'
            
            # Record API usage after successful call with actual model used
            usage_tracker.record_api_call('default_user', model_name, tokens_in=1500, tokens_out=100)
            
            audit_logger.logger.info('Card type detected successfully', extra={
                'event': 'card_type_detected',
                'card_type': card_type,
                'confidence': confidence
            })
            
            return card_type, confidence
        else:
            audit_logger.logger.warning('Failed to parse Gemini response for card type', extra={'event': 'card_type_parse_failed'})
            return 'Other', 0.0
            
    except Exception as e:
        audit_logger.logger.error(f'Error detecting card type: {str(e)}', extra={'event': 'card_type_error', 'error': str(e)})
        return 'Other', 0.0


@retry_api_call
def extract_card_text(pil_img: Image.Image, card_type: str = None, 
                      api_key: str = None) -> Dict[str, any]:
    """
    Extract labeled text fields from an identification card using Gemini Vision API.
    
    Args:
        pil_img: PIL Image object of the ID card
        card_type: Type of card (for targeted field extraction)
        api_key: Gemini API key (if not already configured)
    
    Returns:
        Dictionary with extracted fields and metadata in format:
        {
            "text_fields": {
                "field_name": "extracted_value",
                ...
            },
            "raw_ocr": "full text extracted from card",
            "confidence": 0.0-1.0,
            "success": True/False,
            "message": "status message"
        }
    """
    if not _have_gemini or pil_img is None:
        audit_logger.logger.warning('Text extraction unavailable', extra={
            'event': 'text_extraction_unavailable',
            'has_gemini': _have_gemini,
            'has_image': pil_img is not None
        })
        return {
            "text_fields": {},
            "raw_ocr": "",
            "confidence": 0.0,
            "success": False,
            "message": "Gemini not available or no image provided"
        }
    
    if api_key:
        if not configure_gemini(api_key):
            audit_logger.logger.error('Failed to configure Gemini in extract_card_text', extra={'event': 'text_extraction_config_failed'})
            return {
                "text_fields": {},
                "raw_ocr": "",
                "confidence": 0.0,
                "success": False,
                "message": "Failed to configure Gemini API"
            }
    
    try:
        # Convert image to base64
        img_base64 = pil_to_base64(pil_img)
        if not img_base64:
            audit_logger.logger.error('Failed to convert image to base64 in extract_card_text', extra={'event': 'text_extraction_image_convert_failed'})
            return {
                "text_fields": {},
                "raw_ocr": "",
                "confidence": 0.0,
                "success": False,
                "message": "Failed to convert image"
            }
        
        # Check quota before making API call
        allowed, quota_info = quota_enforcer.check_quota_before_call('default_user')
        if not allowed:
            audit_logger.logger.warning('API quota exceeded during text extraction', extra={'event': 'text_extraction_quota_exceeded', 'quota_info': quota_info})
            raise create_error('API_LIMIT_EXCEEDED')
        
        # Initialize Gemini model - use proper model name
        model = None
        # Use available model variants (gemini-1.5-flash is not available, use newer versions)
        model_names = [
            'gemini-2.5-flash',      # Try the latest model first
            'gemini-2.0-flash',      # Fallback to 2.0 flash
            'gemini-2.5-pro',        # Fallback to pro version
            'gemini-pro'             # Fallback to basic model
        ]
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                audit_logger.logger.debug(f'Using model: {model_name}', extra={'event': 'model_selected', 'model': model_name})
                break
            except Exception as e:
                audit_logger.logger.debug(f'Model {model_name} not available: {e}')
                continue
        
        if model is None:
            audit_logger.logger.error('No suitable Gemini model available', extra={'event': 'no_model_available'})
            return {
                "text_fields": {},
                "raw_ocr": "",
                "confidence": 0.0,
                "success": False,
                "message": "No suitable Gemini model available"
            }
        
        # Create prompt for text extraction
        card_type_hint = f"This is a {card_type}" if card_type else "This is an identification card"
        
        prompt = f"""{card_type_hint}. Extract all visible text and labeled fields from this card.

Use the labels visible on the card (such as 'Name', 'Date of Birth', 'ID Number', 'Address', 'Sex', 'Nationality', 'Expiry Date', etc.) to identify the corresponding values.

For each label found on the card, extract the associated text value. Be precise and only extract what is actually visible on the card.

Respond with a JSON object in this exact format:
{{
    "text_fields": {{
        "label_name": "extracted_value",
        ...
    }},
    "raw_ocr": "all visible text on the card concatenated",
    "fields_confidence": 0.0-1.0,
    "notes": "any important observations"
}}

Example fields might include: name, surname, date_of_birth, id_number, address, sex, nationality, issuing_authority, expiry_date, registration_number, etc."""
        
        # Call Gemini API with vision capabilities
        response = model.generate_content([
            prompt,
            {
                "mime_type": "image/jpeg",
                "data": img_base64
            }
        ])
        
        # Parse response
        response_text = response.text
        
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            # Record API usage after successful call with actual model used
            usage_tracker.record_api_call('default_user', model_name, tokens_in=1500, tokens_out=500)
            
            audit_logger.logger.info('Text extraction successful', extra={
                'event': 'text_extraction_success',
                'fields_count': len(result.get('text_fields', {})),
                'confidence': float(result.get('fields_confidence', 0.0))
            })
            
            return {
                "text_fields": result.get('text_fields', {}),
                "raw_ocr": result.get('raw_ocr', ''),
                "confidence": float(result.get('fields_confidence', 0.0)),
                "success": True,
                "message": "Text extraction successful",
                "notes": result.get('notes', '')
            }
        else:
            audit_logger.logger.warning('Failed to parse Gemini response for text extraction', extra={'event': 'text_extraction_parse_failed'})
            return {
                "text_fields": {},
                "raw_ocr": "",
                "confidence": 0.0,
                "success": False,
                "message": "Failed to parse Gemini response"
            }
            
    except Exception as e:
        audit_logger.logger.error(f'Error extracting card text: {str(e)}', extra={'event': 'text_extraction_error', 'error': str(e)})
        return {
            "text_fields": {},
            "raw_ocr": "",
            "confidence": 0.0,
            "success": False,
            "message": f"Error during extraction: {str(e)}"
        }


@retry_api_call
def analyze_card_complete(pil_img: Image.Image, api_key: str) -> Dict[str, any]:
    """
    Complete card analysis: detect type and extract text in one call.
    
    Args:
        pil_img: PIL Image object of the ID card
        api_key: Gemini API key
    
    Returns:
        Complete analysis result with card type, text fields, and metadata
    """
    if not _have_gemini or pil_img is None:
        audit_logger.logger.warning('Complete card analysis unavailable', extra={
            'event': 'card_analysis_unavailable',
            'has_gemini': _have_gemini,
            'has_image': pil_img is not None
        })
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
            "message": "Gemini not available or no image provided"
        }
    
    # Configure API
    if not configure_gemini(api_key):
        audit_logger.logger.error('Failed to configure Gemini in analyze_card_complete', extra={'event': 'card_analysis_config_failed'})
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
            "message": "Failed to configure Gemini API"
        }
    
    try:
        # Step 1: Detect card type
        card_type, card_confidence = detect_card_type(pil_img)
        
        # Step 2: Extract text with card type hint
        text_result = extract_card_text(pil_img, card_type=card_type)
        
        audit_logger.logger.info('Complete card analysis successful', extra={
            'event': 'card_analysis_success',
            'card_type': card_type,
            'card_confidence': card_confidence,
            'text_success': text_result.get('success')
        })
        
        return {
            "card_type": card_type,
            "card_type_confidence": card_confidence,
            "text_extraction": text_result,
            "success": text_result.get('success', False),
            "message": text_result.get('message', '')
        }
        
    except Exception as e:
        audit_logger.logger.error(f'Error in complete card analysis: {str(e)}', extra={'event': 'card_analysis_error', 'error': str(e)})
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
            "message": f"Error: {str(e)}"
        }

