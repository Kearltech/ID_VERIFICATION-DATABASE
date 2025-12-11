"""
Unit tests for custom exceptions.
"""

import pytest
from exceptions import (
    IDVerificationError,
    APIError,
    CardDetectionError,
    TextExtractionError,
    ValidationError,
    ConfigurationError,
    SecurityError,
    RateLimitError,
    create_error,
    ERROR_CATALOG
)


class TestExceptionBasics:
    """Test basic exception functionality."""
    
    def test_create_base_exception(self):
        """Test creating base exception."""
        exc = IDVerificationError(
            code='TEST_ERROR',
            message='Test error message'
        )
        assert exc.code == 'TEST_ERROR'
        assert exc.message == 'Test error message'
    
    def test_exception_with_details(self):
        """Test exception with details."""
        exc = IDVerificationError(
            code='TEST_ERROR',
            message='Test error',
            details={'field': 'value'}
        )
        assert exc.details == {'field': 'value'}
    
    def test_exception_to_dict(self):
        """Test exception serialization to dict."""
        exc = IDVerificationError(
            code='TEST_ERROR',
            message='Test message',
            user_message='User friendly message'
        )
        exc_dict = exc.to_dict()
        
        assert exc_dict['error_code'] == 'TEST_ERROR'
        assert exc_dict['error_message'] == 'Test message'
        assert exc_dict['user_message'] == 'User friendly message'
    
    def test_exception_str_representation(self):
        """Test string representation of exception."""
        exc = IDVerificationError(
            code='TEST_ERROR',
            message='Test message'
        )
        assert str(exc) == '[TEST_ERROR] Test message'


class TestAPIError:
    """Test API error exceptions."""
    
    def test_create_api_error(self):
        """Test creating API error."""
        exc = APIError(
            code='API_TIMEOUT',
            message='API call timed out'
        )
        assert isinstance(exc, IDVerificationError)
        assert exc.code == 'API_TIMEOUT'
    
    def test_api_error_inheritance(self):
        """Test API error inherits from base."""
        exc = APIError('API_ERROR', 'message')
        assert isinstance(exc, Exception)


class TestCardDetectionError:
    """Test card detection error exceptions."""
    
    def test_create_card_detection_error(self):
        """Test creating card detection error."""
        exc = CardDetectionError(
            code='CARD_NOT_DETECTED',
            message='Could not detect card type'
        )
        assert exc.code == 'CARD_NOT_DETECTED'


class TestErrorCatalog:
    """Test error catalog."""
    
    def test_error_catalog_exists(self):
        """Test that error catalog is defined."""
        assert isinstance(ERROR_CATALOG, dict)
        assert len(ERROR_CATALOG) > 0
    
    def test_error_catalog_has_required_codes(self):
        """Test error catalog has common error codes."""
        required_codes = [
            'API_KEY_INVALID',
            'API_TIMEOUT',
            'CARD_NOT_DETECTED',
            'VALIDATION_FAILED'
        ]
        
        for code in required_codes:
            assert code in ERROR_CATALOG
    
    def test_error_catalog_structure(self):
        """Test error catalog entry structure."""
        entry = ERROR_CATALOG['API_KEY_INVALID']
        
        assert 'message' in entry
        assert 'user_message' in entry
        assert 'action' in entry
    
    def test_all_catalog_entries_have_fields(self):
        """Test all catalog entries have required fields."""
        for code, entry in ERROR_CATALOG.items():
            assert isinstance(entry, dict), f"Entry for {code} is not a dict"
            assert 'message' in entry, f"Entry for {code} missing 'message'"
            assert 'user_message' in entry, f"Entry for {code} missing 'user_message'"
            assert 'action' in entry, f"Entry for {code} missing 'action'"


class TestCreateError:
    """Test create_error factory function."""
    
    def test_create_error_with_catalog_code(self):
        """Test creating error from catalog."""
        exc = create_error('API_KEY_INVALID')
        
        assert exc.code == 'API_KEY_INVALID'
        assert 'API' in exc.message
    
    def test_create_error_with_custom_message(self):
        """Test creating error with custom message."""
        exc = create_error(
            'API_KEY_INVALID',
            message='Custom error message'
        )
        
        assert exc.message == 'Custom error message'
    
    def test_create_error_with_details(self):
        """Test creating error with details."""
        exc = create_error(
            'API_KEY_INVALID',
            details={'key_length': 5}
        )
        
        assert exc.details['key_length'] == 5
    
    def test_create_error_with_custom_class(self):
        """Test creating error with specific exception class."""
        exc = create_error(
            'API_TIMEOUT',
            exception_class=APIError
        )
        
        assert isinstance(exc, APIError)
    
    def test_create_error_unknown_code(self):
        """Test creating error with unknown code."""
        exc = create_error('UNKNOWN_CODE')
        
        # Should default to UNKNOWN_ERROR
        assert exc.code == 'UNKNOWN_ERROR'
    
    def test_create_error_preserves_user_message(self):
        """Test that user message is included."""
        exc = create_error('API_TIMEOUT')
        
        assert exc.user_message is not None
        assert len(exc.user_message) > 0


class TestExceptionTypes:
    """Test different exception types."""
    
    def test_validation_error(self):
        """Test validation error."""
        exc = ValidationError('VALIDATION_FAILED', 'Field validation failed')
        assert isinstance(exc, IDVerificationError)
    
    def test_configuration_error(self):
        """Test configuration error."""
        exc = ConfigurationError('CONFIG_INVALID', 'Invalid config')
        assert isinstance(exc, IDVerificationError)
    
    def test_security_error(self):
        """Test security error."""
        exc = SecurityError('SECURITY_ERROR', 'Security check failed')
        assert isinstance(exc, IDVerificationError)
    
    def test_rate_limit_error(self):
        """Test rate limit error."""
        exc = RateLimitError('API_RATE_LIMIT', 'Rate limit exceeded')
        assert isinstance(exc, IDVerificationError)


class TestExceptionDetails:
    """Test exception detail tracking."""
    
    def test_exception_details_preserved(self):
        """Test that exception details are preserved."""
        details = {
            'field': 'id_number',
            'expected_format': 'GHA-000000000-0',
            'provided_value': 'invalid'
        }
        
        exc = ValidationError(
            'VALIDATION_FAILED',
            'Field validation failed',
            details=details
        )
        
        assert exc.details == details
    
    def test_exception_details_in_dict(self):
        """Test details are included in dict representation."""
        details = {'field': 'test', 'value': '123'}
        
        exc = ValidationError(
            'VALIDATION_FAILED',
            'Failed',
            details=details
        )
        
        exc_dict = exc.to_dict()
        assert exc_dict['details'] == details


class TestUserMessages:
    """Test user-friendly error messages."""
    
    def test_exception_has_user_message(self):
        """Test exceptions have user-friendly messages."""
        exc = create_error('API_TIMEOUT')
        
        assert exc.user_message is not None
        # User message should not contain technical jargon
        assert 'timeout' in exc.user_message.lower() or 'long' in exc.user_message.lower()
    
    def test_user_message_override(self):
        """Test overriding user message."""
        exc = IDVerificationError(
            code='ERROR',
            message='Technical message',
            user_message='User-friendly message'
        )
        
        assert exc.user_message == 'User-friendly message'
        assert exc.message == 'Technical message'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
