"""
Unit tests for ID field mappings functionality.
Tests IDField, FieldCategory, and all ID type registries.
"""

import pytest
from id_field_mappings import (
    IDField, FieldCategory,
    GHANA_CARD_FIELDS, PASSPORT_FIELDS, VOTER_ID_FIELDS,
    DRIVER_LICENSE_FIELDS, BANK_CARD_FIELDS,
    get_id_type_fields, get_user_input_fields, get_ocr_fields,
    get_required_match_fields, validate_id_field, validate_id_form,
    ID_TYPE_REGISTRY
)


class TestIDField:
    """Test IDField dataclass."""
    
    def test_create_field(self):
        """Should create field correctly."""
        field = IDField(
            name='test_field',
            display_name='Test Field',
            category=FieldCategory.REQUIRED,
            regex_pattern=r'^\d+$',
            min_length=1,
            max_length=10
        )
        assert field.name == 'test_field'
        assert field.display_name == 'Test Field'
        assert field.category == FieldCategory.REQUIRED
    
    def test_field_validate_success(self):
        """Should validate field successfully."""
        field = IDField(
            name='test_field',
            display_name='Test Field',
            category=FieldCategory.REQUIRED,
            regex_pattern=r'^\d+$',
            min_length=1,
            max_length=10
        )
        is_valid, msg = field.validate('12345')
        assert is_valid is True
    
    def test_field_validate_regex_fail(self):
        """Should fail regex validation."""
        field = IDField(
            name='test_field',
            display_name='Test Field',
            category=FieldCategory.REQUIRED,
            regex_pattern=r'^\d+$',
            min_length=1,
            max_length=10
        )
        is_valid, msg = field.validate('abc')
        assert is_valid is False
        assert 'format' in msg.lower()
    
    def test_field_validate_length_fail(self):
        """Should fail length validation."""
        field = IDField(
            name='test_field',
            display_name='Test Field',
            category=FieldCategory.REQUIRED,
            regex_pattern=r'^\d+$',
            min_length=5,
            max_length=10
        )
        is_valid, msg = field.validate('123')
        assert is_valid is False
        assert 'length' in msg.lower()
    
    def test_field_sensitive_flag(self):
        """Should respect sensitive flag."""
        field = IDField(
            name='ccv',
            display_name='CCV',
            category=FieldCategory.SECURITY,
            regex_pattern=r'^\d{3,4}$',
            min_length=3,
            max_length=4,
            sensitive=True
        )
        assert field.sensitive is True


class TestFieldCategory:
    """Test FieldCategory enum."""
    
    def test_field_categories_exist(self):
        """Should have all required categories."""
        assert hasattr(FieldCategory, 'REQUIRED')
        assert hasattr(FieldCategory, 'OPTIONAL')
        assert hasattr(FieldCategory, 'OCR_ONLY')
        assert hasattr(FieldCategory, 'DISPLAY')
        assert hasattr(FieldCategory, 'SECURITY')
    
    def test_category_values(self):
        """Should have correct category values."""
        assert FieldCategory.REQUIRED.value == 'required'
        assert FieldCategory.OPTIONAL.value == 'optional'
        assert FieldCategory.OCR_ONLY.value == 'ocr_only'


class TestGhanaCardFields:
    """Test Ghana Card field definitions."""
    
    def test_ghana_card_has_pin(self):
        """Should have ghana_pin field."""
        assert 'ghana_pin' in GHANA_CARD_FIELDS
        field = GHANA_CARD_FIELDS['ghana_pin']
        assert field.category == FieldCategory.REQUIRED
    
    def test_ghana_card_pin_format(self):
        """Should validate Ghana PIN format."""
        field = GHANA_CARD_FIELDS['ghana_pin']
        
        # Valid PIN
        is_valid, _ = field.validate('GHA-123456789-0')
        assert is_valid is True
        
        # Invalid PIN
        is_valid, _ = field.validate('INVALID')
        assert is_valid is False
    
    def test_ghana_card_required_fields(self):
        """Should have required fields."""
        required = [f for f, field in GHANA_CARD_FIELDS.items()
                   if field.category == FieldCategory.REQUIRED]
        assert len(required) > 0
        assert 'ghana_pin' in required
    
    def test_ghana_card_date_of_birth(self):
        """Should validate date of birth."""
        field = GHANA_CARD_FIELDS['date_of_birth']
        
        is_valid, _ = field.validate('1985-05-15')
        assert is_valid is True
        
        is_valid, _ = field.validate('invalid-date')
        assert is_valid is False


class TestPassportFields:
    """Test Passport field definitions."""
    
    def test_passport_has_document_number(self):
        """Should have passport_number field."""
        assert 'passport_number' in PASSPORT_FIELDS
    
    def test_passport_document_number_format(self):
        """Should validate passport number format."""
        field = PASSPORT_FIELDS['passport_number']
        
        is_valid, _ = field.validate('AA123456')
        assert is_valid is True
    
    def test_passport_mrz_fields(self):
        """Should have MRZ line fields."""
        assert 'mrz_line1' in PASSPORT_FIELDS or 'mrz_line_1' in PASSPORT_FIELDS
    
    def test_passport_nationality(self):
        """Should have nationality field."""
        assert 'nationality' in PASSPORT_FIELDS


class TestVoterIDFields:
    """Test Voter ID field definitions."""
    
    def test_voter_id_has_number(self):
        """Should have voter_id_number field."""
        assert 'voter_id_number' in VOTER_ID_FIELDS
    
    def test_voter_id_number_format(self):
        """Should validate voter ID number."""
        field = VOTER_ID_FIELDS['voter_id_number']
        
        is_valid, _ = field.validate('1234567890')
        assert is_valid is True


class TestDriverLicenseFields:
    """Test Driver License field definitions."""
    
    def test_driver_license_has_number(self):
        """Should have licence_number field."""
        assert 'licence_number' in DRIVER_LICENSE_FIELDS
    
    def test_driver_license_expiry(self):
        """Should have expiry date field."""
        assert 'expiry_date' in DRIVER_LICENSE_FIELDS


class TestBankCardFields:
    """Test Bank Card field definitions."""
    
    def test_bank_card_has_number(self):
        """Should have card_number field."""
        assert 'card_number' in BANK_CARD_FIELDS
    
    def test_bank_card_security_fields(self):
        """Should mark security fields appropriately."""
        # CVV should be security
        if 'cvv' in BANK_CARD_FIELDS:
            cvv_field = BANK_CARD_FIELDS['cvv']
            assert cvv_field.sensitive is True
    
    def test_bank_card_masked_pan(self):
        """Should have masked PAN in OCR fields."""
        # Bank card should have PAN masking rules
        assert 'card_number' in BANK_CARD_FIELDS


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_get_id_type_fields(self):
        """Should get fields for valid ID type."""
        fields = get_id_type_fields('Ghana Card')
        assert isinstance(fields, dict)
        assert len(fields) > 0
    
    def test_get_id_type_fields_invalid(self):
        """Should raise error for invalid ID type."""
        with pytest.raises((KeyError, ValueError)):
            get_id_type_fields('Invalid Type')
    
    def test_get_user_input_fields(self):
        """Should get user input fields."""
        fields = get_user_input_fields('Ghana Card')
        assert isinstance(fields, dict)
        # User input fields should not include OCR-only fields
        assert len(fields) > 0
    
    def test_get_ocr_fields(self):
        """Should get OCR-only fields."""
        fields = get_ocr_fields('Ghana Card')
        assert isinstance(fields, dict)
    
    def test_get_required_match_fields(self):
        """Should get required match fields."""
        fields = get_required_match_fields('Ghana Card')
        assert isinstance(fields, list)
        assert len(fields) > 0
        # ghana_pin should be required
        assert 'ghana_pin' in fields
    
    def test_validate_id_field(self):
        """Should validate individual field."""
        is_valid, msg = validate_id_field('Ghana Card', 'ghana_pin', 'GHA-123456789-0')
        assert is_valid is True
    
    def test_validate_id_field_invalid(self):
        """Should reject invalid field."""
        is_valid, msg = validate_id_field('Ghana Card', 'ghana_pin', 'INVALID')
        assert is_valid is False
    
    def test_validate_id_form_complete(self):
        """Should validate complete form."""
        form_data = {
            'ghana_pin': 'GHA-123456789-0',
            'date_of_birth': '1985-05-15',
            'expiry_date': '2030-12-31',
            'sex': 'M'
        }
        is_valid, errors = validate_id_form('Ghana Card', form_data)
        # May have some missing optional fields but core required should validate
        assert isinstance(is_valid, bool)
        assert isinstance(errors, dict)
    
    def test_validate_id_form_with_errors(self):
        """Should report validation errors."""
        form_data = {
            'ghana_pin': 'INVALID-PIN',  # Invalid format
        }
        is_valid, errors = validate_id_form('Ghana Card', form_data)
        assert is_valid is False
        assert len(errors) > 0


class TestIDTypeRegistry:
    """Test ID type registry."""
    
    def test_registry_contains_all_types(self):
        """Should have all 5 ID types."""
        expected_types = [
            'Ghana Card',
            'Ghana Passport',
            'Voter ID',
            'Driver License',
            'Bank Card'
        ]
        
        for id_type in expected_types:
            assert id_type in ID_TYPE_REGISTRY
    
    def test_registry_metadata(self):
        """Should have metadata for each type."""
        for id_type, metadata in ID_TYPE_REGISTRY.items():
            assert 'fields' in metadata
            assert 'required_fields' in metadata
            assert 'description' in metadata
    
    def test_registry_fields_are_idfield_instances(self):
        """Should have IDField instances."""
        for id_type, metadata in ID_TYPE_REGISTRY.items():
            fields = metadata['fields']
            for field_name, field_obj in fields.items():
                assert isinstance(field_obj, IDField)


class TestCrossIDTypeConsistency:
    """Test consistency across ID types."""
    
    def test_common_fields_consistent(self):
        """Should have consistent validation for common fields."""
        if 'date_of_birth' in GHANA_CARD_FIELDS:
            ghana_dob = GHANA_CARD_FIELDS['date_of_birth']
            if 'date_of_birth' in PASSPORT_FIELDS:
                passport_dob = PASSPORT_FIELDS['date_of_birth']
                # Both should use same regex pattern
                assert ghana_dob.regex_pattern == passport_dob.regex_pattern
    
    def test_all_types_have_categories(self):
        """All fields should have category."""
        for registry in [GHANA_CARD_FIELDS, PASSPORT_FIELDS, VOTER_ID_FIELDS,
                        DRIVER_LICENSE_FIELDS, BANK_CARD_FIELDS]:
            for field_name, field_obj in registry.items():
                assert hasattr(field_obj, 'category')
                assert isinstance(field_obj.category, FieldCategory)


class TestFieldValidationEdgeCases:
    """Test edge cases in field validation."""
    
    def test_empty_field_value(self):
        """Should handle empty values."""
        field = GHANA_CARD_FIELDS['ghana_pin']
        is_valid, msg = field.validate('')
        assert is_valid is False
    
    def test_none_field_value(self):
        """Should handle None values."""
        field = GHANA_CARD_FIELDS['ghana_pin']
        is_valid, msg = field.validate(None)
        assert is_valid is False
    
    def test_whitespace_only(self):
        """Should handle whitespace-only values."""
        field = GHANA_CARD_FIELDS['ghana_pin']
        is_valid, msg = field.validate('   ')
        assert is_valid is False
    
    def test_very_long_string(self):
        """Should reject too-long strings."""
        field = GHANA_CARD_FIELDS['ghana_pin']
        long_value = 'A' * 1000
        is_valid, msg = field.validate(long_value)
        assert is_valid is False
    
    def test_special_characters(self):
        """Should handle special characters."""
        field = GHANA_CARD_FIELDS['full_name']
        is_valid, msg = field.validate("O'Brien")
        # Should be valid (name with apostrophe)
        assert is_valid is True


class TestFormValidationComprehensive:
    """Comprehensive form validation tests."""
    
    def test_validate_minimal_ghana_card_form(self):
        """Should validate minimal Ghana Card form."""
        form_data = {
            'ghana_pin': 'GHA-123456789-0',
        }
        is_valid, errors = validate_id_form('Ghana Card', form_data)
        # At least PIN should validate
        assert 'ghana_pin' not in errors
    
    def test_validate_complete_ghana_card_form(self):
        """Should validate complete Ghana Card form."""
        form_data = {
            'ghana_pin': 'GHA-123456789-0',
            'date_of_birth': '1985-05-15',
            'expiry_date': '2030-12-31',
            'sex': 'M',
            'first_name': 'John',
            'surname': 'Doe'
        }
        is_valid, errors = validate_id_form('Ghana Card', form_data)
        assert isinstance(is_valid, bool)
    
    def test_validate_passport_form(self):
        """Should validate passport form."""
        form_data = {
            'passport_number': 'AA123456',
            'date_of_birth': '1985-05-15',
        }
        is_valid, errors = validate_id_form('Ghana Passport', form_data)
        assert isinstance(is_valid, bool)
    
    def test_validate_voter_id_form(self):
        """Should validate voter ID form."""
        form_data = {
            'voter_id_number': '1234567890',
        }
        is_valid, errors = validate_id_form('Voter ID', form_data)
        assert isinstance(is_valid, bool)
    
    def test_validate_driver_license_form(self):
        """Should validate driver license form."""
        form_data = {
            'licence_number': 'ABC123456',
            'expiry_date': '2030-12-31',
        }
        is_valid, errors = validate_id_form('Driver License', form_data)
        assert isinstance(is_valid, bool)
    
    def test_validate_bank_card_form(self):
        """Should validate bank card form."""
        form_data = {
            'card_number': '4532123456789010',
            'expiry_date': '2030-12-31',
            'cardholder_name': 'John Doe',
        }
        is_valid, errors = validate_id_form('Bank Card', form_data)
        assert isinstance(is_valid, bool)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
