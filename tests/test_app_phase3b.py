"""
Phase 3B Integration Tests for Streamlit App

Tests dynamic form generation, ID-type-specific validation,
and OCR comparison UI integration in app.py
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from id_field_mappings import (
    get_user_input_fields,
    get_id_type_fields,
    ID_TYPE_REGISTRY,
    FieldCategory
)
from ocr_comparison import compare_user_input_with_ocr
from verify import compare_ocr_with_user_input
from validators import InputValidator


class TestDynamicFormGeneration(unittest.TestCase):
    """Test dynamic form generation based on ID type"""
    
    def test_ghana_card_form_fields(self):
        """Test form fields generated for Ghana Card"""
        fields = get_user_input_fields('ghana_card')
        
        # Should have required and optional fields
        self.assertIn('ghana_pin', fields)
        self.assertIn('full_name', fields)
        self.assertIn('date_of_birth', fields)
        self.assertIn('date_of_issue', fields)
        self.assertIn('date_of_expiry', fields)
        self.assertIn('sex', fields)
        
        # Should NOT have OCR_ONLY or DISPLAY fields
        for field_name, field_obj in fields.items():
            self.assertNotIn(field_obj.category, [FieldCategory.OCR_ONLY, FieldCategory.DISPLAY])
    
    def test_passport_form_fields(self):
        """Test form fields generated for Passport"""
        fields = get_user_input_fields('passport')
        
        # Should have passport-specific fields
        self.assertIn('passport_number', fields)
        self.assertIn('surname', fields)
        self.assertIn('given_names', fields)
        self.assertIn('nationality', fields)
        self.assertIn('date_of_birth', fields)
        self.assertIn('date_of_issue', fields)
        self.assertIn('date_of_expiry', fields)
        self.assertIn('sex', fields)
        
        # Should have place of birth as optional
        self.assertIn('place_of_birth', fields)
    
    def test_voter_id_form_fields(self):
        """Test form fields generated for Voter ID"""
        fields = get_user_input_fields('voter_id')
        
        # Should have voter-specific fields
        self.assertIn('voter_id_number', fields)
        self.assertIn('full_name', fields)
        self.assertIn('date_of_birth', fields)
        self.assertIn('date_of_registration', fields)
        self.assertIn('sex', fields)
        self.assertIn('polling_station', fields)
    
    def test_drivers_licence_form_fields(self):
        """Test form fields generated for Driver's Licence"""
        fields = get_user_input_fields('drivers_licence')
        
        # Should have licence-specific fields
        self.assertIn('licence_number', fields)
        self.assertIn('full_name', fields)
        self.assertIn('date_of_birth', fields)
        self.assertIn('date_of_issue', fields)
        self.assertIn('date_of_expiry', fields)
        self.assertIn('licence_class', fields)
        self.assertIn('sex', fields)
    
    def test_bank_card_form_fields(self):
        """Test form fields generated for Bank Card"""
        fields = get_user_input_fields('bank_card')
        
        # Should have card-specific fields
        self.assertIn('card_number', fields)
        self.assertIn('cardholder_name', fields)
        self.assertIn('expiry_date', fields)
        self.assertIn('cvv', fields)
        
        # CVV should be marked as sensitive
        self.assertTrue(fields['cvv'].sensitive)
        self.assertEqual(fields['cvv'].category, FieldCategory.SECURITY)
    
    def test_all_id_types_have_forms(self):
        """Test that all ID types in registry can generate forms"""
        for id_type in ID_TYPE_REGISTRY.keys():
            fields = get_user_input_fields(id_type)
            self.assertIsNotNone(fields, f"No fields generated for {id_type}")
            self.assertGreater(len(fields), 0, f"Empty fields for {id_type}")
    
    def test_field_categories_filter(self):
        """Test that user input fields exclude OCR_ONLY and DISPLAY"""
        for id_type in ID_TYPE_REGISTRY.keys():
            fields = get_user_input_fields(id_type)
            for field_name, field_obj in fields.items():
                self.assertNotIn(
                    field_obj.category,
                    [FieldCategory.OCR_ONLY, FieldCategory.DISPLAY],
                    f"{id_type}.{field_name} should not be in user input form"
                )


class TestIDTypeValidation(unittest.TestCase):
    """Test ID-type-specific validation in app context"""
    
    def setUp(self):
        self.validator = InputValidator()
    
    def test_ghana_card_validation(self):
        """Test validation with Ghana Card ID type"""
        form_data = {
            'ghana_pin': 'GHA-123456789-0',
            'full_name': 'John Doe',
            'date_of_birth': '1990-01-01',
            'date_of_issue': '2020-01-01',
            'date_of_expiry': '2030-01-01',
            'sex': 'M'
        }
        
        is_valid, cleaned_data, errors = self.validator.validate_form_data(
            form_data, id_type='ghana_card'
        )
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        self.assertEqual(cleaned_data['ghana_pin'], 'GHA-123456789-0')
    
    def test_passport_validation(self):
        """Test validation with Passport ID type"""
        form_data = {
            'passport_number': 'G1234567',
            'surname': 'Doe',
            'given_names': 'John',
            'nationality': 'Ghanaian',
            'date_of_birth': '1990-01-01',
            'date_of_issue': '2020-01-01',
            'date_of_expiry': '2030-01-01',
            'sex': 'M'
        }
        
        is_valid, cleaned_data, errors = self.validator.validate_form_data(
            form_data, id_type='passport'
        )
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_invalid_ghana_pin_format(self):
        """Test that invalid Ghana PIN format is caught"""
        form_data = {
            'ghana_pin': 'INVALID',
            'full_name': 'John Doe',
            'date_of_birth': '1990-01-01',
            'sex': 'M'
        }
        
        is_valid, cleaned_data, errors = self.validator.validate_form_data(
            form_data, id_type='ghana_card'
        )
        
        self.assertFalse(is_valid)
        self.assertIn('ghana_pin', errors)
    
    def test_missing_required_field(self):
        """Test that missing required fields are caught"""
        form_data = {
            'full_name': 'John Doe',
            'date_of_birth': '1990-01-01'
            # Missing ghana_pin (required)
        }
        
        is_valid, cleaned_data, errors = self.validator.validate_form_data(
            form_data, id_type='ghana_card'
        )
        
        self.assertFalse(is_valid)
        self.assertIn('ghana_pin', errors)
    
    def test_fallback_validation_for_unknown_id_type(self):
        """Test that validation falls back for unknown ID types"""
        form_data = {
            'some_field': 'some value'
        }
        
        # Should not crash, should use fallback rules
        is_valid, cleaned_data, errors = self.validator.validate_form_data(
            form_data, id_type='unknown_type'
        )
        
        # Will fail validation but won't crash
        self.assertIsNotNone(cleaned_data)


class TestOCRComparisonIntegration(unittest.TestCase):
    """Test OCR comparison integration in app"""
    
    def test_successful_comparison(self):
        """Test successful OCR comparison"""
        user_data = {
            'ghana_pin': 'GHA-123456789-0',
            'full_name': 'John Doe',
            'date_of_birth': '1990-01-01',
            'sex': 'M'
        }
        
        ocr_data = {
            'ghana_pin': 'GHA-123456789-0',
            'full_name': 'John Doe',
            'date_of_birth': '01/01/1990',  # Different format
            'sex': 'Male'  # Different format
        }
        
        result = compare_ocr_with_user_input('ghana_card', user_data, ocr_data)
        
        self.assertTrue(result['valid'])
        self.assertGreater(len(result['passed_fields']), 0)
        self.assertEqual(len(result['failed_fields']), 0)
    
    def test_failed_comparison(self):
        """Test failed OCR comparison with mismatches"""
        user_data = {
            'ghana_pin': 'GHA-123456789-0',
            'full_name': 'John Doe',
            'date_of_birth': '1990-01-01'
        }
        
        ocr_data = {
            'ghana_pin': 'GHA-999999999-9',  # Different PIN
            'full_name': 'Jane Smith',  # Different name
            'date_of_birth': '1995-05-05'  # Different DOB
        }
        
        result = compare_ocr_with_user_input('ghana_card', user_data, ocr_data)
        
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['failed_fields']), 0)
    
    def test_missing_ocr_fields(self):
        """Test comparison with missing OCR fields"""
        user_data = {
            'ghana_pin': 'GHA-123456789-0',
            'full_name': 'John Doe',
            'date_of_birth': '1990-01-01'
        }
        
        ocr_data = {
            'ghana_pin': 'GHA-123456789-0'
            # Missing full_name and date_of_birth
        }
        
        result = compare_ocr_with_user_input('ghana_card', user_data, ocr_data)
        
        self.assertGreater(len(result['missing_fields']), 0)
        self.assertIn('full_name', result['missing_fields'])
    
    def test_comparison_details_structure(self):
        """Test that comparison result has proper structure"""
        user_data = {
            'ghana_pin': 'GHA-123456789-0',
            'full_name': 'John Doe'
        }
        
        ocr_data = {
            'ghana_pin': 'GHA-123456789-0',
            'full_name': 'John Doe'
        }
        
        result = compare_ocr_with_user_input('ghana_card', user_data, ocr_data)
        
        # Check structure
        self.assertIn('valid', result)
        self.assertIn('passed_fields', result)
        self.assertIn('failed_fields', result)
        self.assertIn('missing_fields', result)
        self.assertIn('details', result)
        self.assertIn('message', result)
        
        # Check types
        self.assertIsInstance(result['valid'], bool)
        self.assertIsInstance(result['passed_fields'], list)
        self.assertIsInstance(result['failed_fields'], list)
        self.assertIsInstance(result['missing_fields'], list)
        self.assertIsInstance(result['details'], dict)
        self.assertIsInstance(result['message'], str)


class TestFormFieldTypes(unittest.TestCase):
    """Test field type detection for UI rendering"""
    
    def test_gender_field_detection(self):
        """Test that gender/sex fields are detected"""
        fields = get_user_input_fields('ghana_card')
        sex_field = fields.get('sex')
        
        self.assertIsNotNone(sex_field)
        # App should render this as selectbox
        self.assertIn('sex', sex_field.field_name.lower())
    
    def test_date_field_detection(self):
        """Test that date fields are detected"""
        fields = get_user_input_fields('ghana_card')
        
        date_fields = [
            name for name in fields.keys()
            if 'date' in name.lower()
        ]
        
        self.assertGreater(len(date_fields), 0)
        # App should show date format hint for these
    
    def test_sensitive_field_detection(self):
        """Test that sensitive fields are marked"""
        fields = get_user_input_fields('bank_card')
        cvv_field = fields.get('cvv')
        
        self.assertIsNotNone(cvv_field)
        self.assertTrue(cvv_field.sensitive)
        # App should render this as password input
    
    def test_help_text_available(self):
        """Test that fields have help text for UI hints"""
        for id_type in ID_TYPE_REGISTRY.keys():
            fields = get_user_input_fields(id_type)
            for field_name, field_obj in fields.items():
                # Category should be available for help text
                self.assertIsNotNone(field_obj.category)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def test_empty_user_data(self):
        """Test comparison with empty user data"""
        result = compare_ocr_with_user_input('ghana_card', {}, {
            'ghana_pin': 'GHA-123456789-0'
        })
        
        # Should handle gracefully
        self.assertIsNotNone(result)
        self.assertIn('valid', result)
    
    def test_empty_ocr_data(self):
        """Test comparison with empty OCR data"""
        result = compare_ocr_with_user_input('ghana_card', {
            'ghana_pin': 'GHA-123456789-0'
        }, {})
        
        # Should handle gracefully
        self.assertIsNotNone(result)
        self.assertIn('missing_fields', result)
    
    def test_invalid_id_type(self):
        """Test with invalid ID type"""
        # Should handle gracefully without crashing
        try:
            fields = get_user_input_fields('invalid_type')
            # If it returns None or empty, that's acceptable
            self.assertTrue(fields is None or len(fields) == 0)
        except Exception as e:
            self.fail(f"Should handle invalid ID type gracefully: {e}")
    
    def test_special_characters_in_data(self):
        """Test handling of special characters"""
        user_data = {
            'full_name': "O'Brien-McDonald"
        }
        
        ocr_data = {
            'full_name': "O'Brien-McDonald"
        }
        
        result = compare_ocr_with_user_input('ghana_card', user_data, ocr_data)
        
        # Should handle special characters
        self.assertIn('full_name', result['passed_fields'])


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing code"""
    
    def setUp(self):
        self.validator = InputValidator()
    
    def test_validation_without_id_type(self):
        """Test that validation works without id_type parameter"""
        form_data = {
            'full_name': 'John Doe',
            'date_of_birth': '1990-01-01'
        }
        
        # Should work with fallback rules
        is_valid, cleaned_data, errors = self.validator.validate_form_data(form_data)
        
        self.assertIsNotNone(cleaned_data)
        # May or may not be valid, but should not crash
    
    def test_id_type_registry_structure(self):
        """Test that ID_TYPE_REGISTRY has expected structure"""
        for id_type, config in ID_TYPE_REGISTRY.items():
            self.assertIn('display_name', config)
            self.assertIn('description', config)
            self.assertIn('fields', config)
            self.assertIsInstance(config['fields'], dict)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
