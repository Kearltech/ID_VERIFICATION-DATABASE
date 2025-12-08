"""
Custom exceptions for the ID Verification system.
Provides structured error handling with error codes and details.
"""

from typing import Dict, Any, Optional


class IDVerificationError(Exception):
    """Base exception for ID verification system."""
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        """
        Initialize exception.
        
        Args:
            code: Error code (e.g., 'API_KEY_INVALID')
            message: Technical error message for logging
            details: Additional context for debugging
            user_message: User-friendly message
        """
        self.code = code
        self.message = message
        self.details = details or {}
        self.user_message = user_message or message
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'error_code': self.code,
            'error_message': self.message,
            'user_message': self.user_message,
            'details': self.details
        }
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class APIError(IDVerificationError):
    """Raised when API call fails."""
    pass


class CardDetectionError(IDVerificationError):
    """Raised when card detection fails."""
    pass


class TextExtractionError(IDVerificationError):
    """Raised when text extraction fails."""
    pass


class ValidationError(IDVerificationError):
    """Raised when validation fails."""
    pass


class ConfigurationError(IDVerificationError):
    """Raised when configuration is invalid."""
    pass


class SecurityError(IDVerificationError):
    """Raised when security check fails."""
    pass


class RateLimitError(IDVerificationError):
    """Raised when rate limit is exceeded."""
    pass


# Error messages and codes
ERROR_CATALOG = {
    'API_KEY_INVALID': {
        'message': 'Invalid or missing API key',
        'user_message': 'Configuration error: Invalid API key. Please check your Gemini API configuration.',
        'action': 'Verify API key is set correctly. Contact support with code API_001 if issue persists.'
    },
    'API_TIMEOUT': {
        'message': 'API request timed out',
        'user_message': 'The card analysis took too long. Please try again with a clearer image.',
        'action': 'Check your internet connection and try uploading a clearer, well-lit image.'
    },
    'API_RATE_LIMIT': {
        'message': 'Rate limit exceeded',
        'user_message': 'Too many requests. Please wait a moment before trying again.',
        'action': 'Wait a few minutes and try again. Check your API quota.'
    },
    'API_QUOTA_EXCEEDED': {
        'message': 'Monthly API quota exceeded',
        'user_message': 'API usage limit reached for this month.',
        'action': 'Wait until next billing period or upgrade your API plan.'
    },
    'API_INVALID_RESPONSE': {
        'message': 'API returned invalid response',
        'user_message': 'Service error. Please try again.',
        'action': 'Retry the operation. If error persists, contact support.'
    },
    'IMAGE_INVALID': {
        'message': 'Image could not be processed',
        'user_message': 'The uploaded image could not be read. Please ensure it is a valid image file.',
        'action': 'Try uploading a different image file (PNG, JPG, JPEG).'
    },
    'IMAGE_TOO_LARGE': {
        'message': 'Image exceeds size limit',
        'user_message': 'Image is too large. Maximum size is 10MB.',
        'action': 'Compress the image and try again.'
    },
    'CARD_NOT_DETECTED': {
        'message': 'Could not identify card type',
        'user_message': 'Could not recognize the card type from the image.',
        'action': 'Ensure the entire card is visible, well-lit, and in focus.'
    },
    'CARD_CONFIDENCE_LOW': {
        'message': 'Card detection confidence too low',
        'user_message': 'The card type could not be reliably identified.',
        'action': 'Try with a better quality image - ensure good lighting and focus.'
    },
    'TEXT_EXTRACTION_FAILED': {
        'message': 'Failed to extract text from card',
        'user_message': 'Could not read the text on the card.',
        'action': 'Ensure the card text is clearly visible and legible in the image.'
    },
    'TEXT_EXTRACTION_INCOMPLETE': {
        'message': 'Text extraction incomplete - some fields missing',
        'user_message': 'Some text could not be extracted from the card.',
        'action': 'Verify important fields manually or upload a clearer image.'
    },
    'VALIDATION_FAILED': {
        'message': 'Field validation failed',
        'user_message': 'Some fields did not pass validation.',
        'action': 'Review the validation errors and correct the data.'
    },
    'FACE_MATCH_FAILED': {
        'message': 'Face matching failed',
        'user_message': 'Could not compare the portrait with the ID card photo.',
        'action': 'Ensure both images contain clear, forward-facing faces.'
    },
    'FACE_NO_MATCH': {
        'message': 'Faces do not match',
        'user_message': 'The portrait does not match the face on the ID card.',
        'action': 'Verify you uploaded the correct portrait and ID card images.'
    },
    'INPUT_VALIDATION_ERROR': {
        'message': 'Input validation failed',
        'user_message': 'Invalid input format.',
        'action': 'Check the input format and try again.'
    },
    'SECURITY_ERROR': {
        'message': 'Security check failed',
        'user_message': 'A security check failed.',
        'action': 'This may indicate a security issue. Contact support.'
    },
    'CONFIG_MISSING': {
        'message': 'Required configuration missing',
        'user_message': 'System not properly configured.',
        'action': 'Contact system administrator.'
    },
    'CONFIG_INVALID': {
        'message': 'Invalid configuration value',
        'user_message': 'System configuration error.',
        'action': 'Contact system administrator.'
    },
    'DATABASE_ERROR': {
        'message': 'Database operation failed',
        'user_message': 'Could not save submission.',
        'action': 'Please try again. If error persists, contact support.'
    },
    'UNKNOWN_ERROR': {
        'message': 'An unexpected error occurred',
        'user_message': 'An unexpected error occurred.',
        'action': 'Please try again. Contact support if the issue persists.'
    }
}


def create_error(
    code: str,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    exception_class: type = IDVerificationError
) -> IDVerificationError:
    """
    Create an exception with standardized error information.
    
    Args:
        code: Error code from ERROR_CATALOG
        message: Override message (uses catalog if not provided)
        details: Additional debugging details
        exception_class: Exception class to instantiate
    
    Returns:
        Configured exception instance
    """
    if code not in ERROR_CATALOG:
        code = 'UNKNOWN_ERROR'
    
    catalog_entry = ERROR_CATALOG[code]
    
    return exception_class(
        code=code,
        message=message or catalog_entry['message'],
        details=details or {},
        user_message=catalog_entry['user_message']
    )


if __name__ == "__main__":
    # Test exception creation
    exc = create_error('API_KEY_INVALID', details={'key_length': 0})
    print(f"Exception: {exc}")
    print(f"Error dict: {exc.to_dict()}")
    print(f"User message: {exc.user_message}")
