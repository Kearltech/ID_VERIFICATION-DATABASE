"""
Unit tests for input validators.
"""

import pytest
from datetime import datetime, timedelta
from validators import InputValidator


class TestInputValidatorBasic:
    """Test basic input validation."""
    
    def test_sanitize_input_basic(self):
        """Test basic input sanitization."""
        result = InputValidator.sanitize_input("  hello  ")
        assert result == "hello"
    
    def test_sanitize_input_long_string(self):
        """Test truncation of long strings."""
        long_string = "a" * 1000
        result = InputValidator.sanitize_input(long_string, max_length=100)
        assert len(result) == 100
    
    def test_sanitize_input_empty(self):
        """Test empty input."""
        result = InputValidator.sanitize_input("")
        assert result == ""


class TestGhanaPINValidation:
    """Test Ghana PIN validation."""
    
    def test_valid_ghana_pin(self):
        """Test valid Ghana PIN format."""
        is_valid, msg = InputValidator.validate_ghana_pin("GHA-123456789-0")
        assert is_valid is True
        assert "Valid" in msg
    
    def test_invalid_ghana_pin_format(self):
        """Test invalid Ghana PIN format."""
        is_valid, msg = InputValidator.validate_ghana_pin("GHA-12345678-0")
        assert is_valid is False
    
    def test_invalid_ghana_pin_missing_prefix(self):
        """Test Ghana PIN without prefix."""
        is_valid, msg = InputValidator.validate_ghana_pin("123456789-0")
        assert is_valid is False
    
    def test_invalid_ghana_pin_non_string(self):
        """Test non-string Ghana PIN."""
        is_valid, msg = InputValidator.validate_ghana_pin(12345)
        assert is_valid is False
    
    def test_valid_ghana_pin_with_spaces(self):
        """Test Ghana PIN with surrounding spaces."""
        is_valid, msg = InputValidator.validate_ghana_pin("  GHA-123456789-0  ")
        assert is_valid is True


class TestVoterIDValidation:
    """Test Voter ID validation."""
    
    def test_valid_voter_id(self):
        """Test valid Voter ID."""
        is_valid, msg = InputValidator.validate_voter_id("1234567890")
        assert is_valid is True
    
    def test_invalid_voter_id_too_short(self):
        """Test Voter ID too short."""
        is_valid, msg = InputValidator.validate_voter_id("12345678")
        assert is_valid is False
    
    def test_invalid_voter_id_contains_letters(self):
        """Test Voter ID with letters."""
        is_valid, msg = InputValidator.validate_voter_id("123456789A")
        assert is_valid is False
    
    def test_invalid_voter_id_non_string(self):
        """Test non-string Voter ID."""
        is_valid, msg = InputValidator.validate_voter_id(1234567890)
        assert is_valid is False


class TestDriverLicenseValidation:
    """Test Driver's License validation."""
    
    def test_valid_driver_license(self):
        """Test valid driver's license."""
        is_valid, msg = InputValidator.validate_driver_license("DL-12345")
        assert is_valid is True
    
    def test_valid_driver_license_with_slash(self):
        """Test license with slashes."""
        is_valid, msg = InputValidator.validate_driver_license("DL/12345/A")
        assert is_valid is True
    
    def test_invalid_driver_license_too_short(self):
        """Test license too short."""
        is_valid, msg = InputValidator.validate_driver_license("DL")
        assert is_valid is False
    
    def test_invalid_driver_license_special_chars(self):
        """Test license with invalid special characters."""
        is_valid, msg = InputValidator.validate_driver_license("DL@12345")
        assert is_valid is False


class TestPassportValidation:
    """Test Passport number validation."""
    
    def test_valid_passport_number(self):
        """Test valid passport number."""
        is_valid, msg = InputValidator.validate_passport_number("A12345")
        assert is_valid is True
    
    def test_valid_passport_number_long(self):
        """Test long passport number."""
        is_valid, msg = InputValidator.validate_passport_number("ABC123XYZ456")
        assert is_valid is True
    
    def test_invalid_passport_too_short(self):
        """Test passport number too short."""
        is_valid, msg = InputValidator.validate_passport_number("AB12")
        assert is_valid is False
    
    def test_invalid_passport_special_chars(self):
        """Test passport with special characters."""
        is_valid, msg = InputValidator.validate_passport_number("A12@45")
        assert is_valid is False


class TestDateValidation:
    """Test date of birth validation."""
    
    def test_valid_date_of_birth(self):
        """Test valid date of birth."""
        is_valid, msg = InputValidator.validate_field(
            'date_of_birth',
            '1990-05-15'
        )
        assert is_valid is True
    
    def test_date_of_birth_future_date(self):
        """Test future date as birth date."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        is_valid, msg = InputValidator.validate_field(
            'date_of_birth',
            tomorrow
        )
        assert is_valid is False
    
    def test_date_of_birth_too_old(self):
        """Test unrealistic old date."""
        is_valid, msg = InputValidator.validate_field(
            'date_of_birth',
            '1800-01-01'
        )
        assert is_valid is False
    
    def test_date_of_birth_too_young(self):
        """Test person too young."""
        today = datetime.now()
        young_date = (today - timedelta(days=365*5)).strftime('%Y-%m-%d')
        is_valid, msg = InputValidator.validate_field(
            'date_of_birth',
            young_date
        )
        assert is_valid is False
    
    def test_invalid_date_format(self):
        """Test invalid date format."""
        is_valid, msg = InputValidator.validate_field(
            'date_of_birth',
            '05/15/1990'
        )
        assert is_valid is False


class TestNameValidation:
    """Test name field validation."""
    
    def test_valid_name(self):
        """Test valid name."""
        is_valid, msg = InputValidator.validate_field('name', 'John Doe')
        assert is_valid is True
    
    def test_valid_name_with_apostrophe(self):
        """Test name with apostrophe."""
        is_valid, msg = InputValidator.validate_field('name', "O'Brien")
        assert is_valid is True
    
    def test_valid_name_with_hyphen(self):
        """Test hyphenated name."""
        is_valid, msg = InputValidator.validate_field('name', 'Mary-Jane')
        assert is_valid is True
    
    def test_invalid_name_too_short(self):
        """Test name too short."""
        is_valid, msg = InputValidator.validate_field('name', 'A')
        assert is_valid is False
    
    def test_invalid_name_with_numbers(self):
        """Test name with numbers."""
        is_valid, msg = InputValidator.validate_field('name', 'John123')
        assert is_valid is False
    
    def test_invalid_name_with_special_chars(self):
        """Test name with special characters."""
        is_valid, msg = InputValidator.validate_field('name', 'John@Doe')
        assert is_valid is False


class TestFormDataValidation:
    """Test complete form data validation."""
    
    def test_valid_form_data(self):
        """Test valid complete form."""
        form_data = {
            'id_number': 'GHA-123456789-0',
            'surname': 'Doe',
            'firstname': 'John',
            'date_of_birth': '1990-05-15',
            'sex': 'M'
        }
        
        all_valid, errors, cleaned = InputValidator.validate_form_data(form_data)
        assert all_valid is True
        assert len(errors) == 0
        assert 'surname' in cleaned
    
    def test_invalid_form_data_multiple_errors(self):
        """Test form with multiple validation errors."""
        form_data = {
            'id_number': 'INVALID',
            'surname': 'X',  # Too short
            'firstname': 'John123',  # Invalid chars
            'date_of_birth': '2024-01-01',  # Future date
            'sex': 'X'  # Invalid value
        }
        
        all_valid, errors, cleaned = InputValidator.validate_form_data(form_data)
        assert all_valid is False
        assert len(errors) > 0
    
    def test_form_with_optional_fields_empty(self):
        """Test form with empty optional fields."""
        form_data = {
            'id_number': 'GHA-123456789-0',
            'surname': 'Doe',
            'firstname': '',  # Empty
            'date_of_birth': '1990-05-15',
        }
        
        all_valid, errors, cleaned = InputValidator.validate_form_data(form_data)
        # Empty values are skipped
        assert 'firstname' not in cleaned
    
    def test_form_data_sanitization(self):
        """Test that form data is sanitized."""
        form_data = {
            'surname': '  Doe  ',  # Extra spaces
            'firstname': '  John  ',
        }
        
        all_valid, errors, cleaned = InputValidator.validate_form_data(form_data)
        assert cleaned['surname'] == 'Doe'
        assert cleaned['firstname'] == 'John'


class TestSexValidation:
    """Test sex/gender field validation."""
    
    def test_valid_sex_male(self):
        """Test valid male designation."""
        is_valid, msg = InputValidator.validate_field('sex', 'M')
        assert is_valid is True
    
    def test_valid_sex_female(self):
        """Test valid female designation."""
        is_valid, msg = InputValidator.validate_field('sex', 'F')
        assert is_valid is True
    
    def test_valid_sex_other(self):
        """Test valid other designation."""
        is_valid, msg = InputValidator.validate_field('sex', 'O')
        assert is_valid is True
    
    def test_invalid_sex(self):
        """Test invalid sex value."""
        is_valid, msg = InputValidator.validate_field('sex', 'X')
        assert is_valid is False
    
    def test_invalid_sex_lowercase(self):
        """Test lowercase sex value."""
        is_valid, msg = InputValidator.validate_field('sex', 'm')
        assert is_valid is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
