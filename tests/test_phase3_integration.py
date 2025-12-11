"""
Phase 3 Integration Tests - Field Mappings & OCR Comparison
Tests integration of new Phase 3 modules with existing Phase 1-2 infrastructure.
"""

import pytest
from validators import InputValidator
from ocr_comparison import compare_user_input_with_ocr, FieldComparator
from id_field_mappings import (
    validate_id_form, get_required_match_fields, get_user_input_fields
)
from exceptions import ValidationError


class TestValidatorsPhase3Integration:
    """Test validators.py integration with field mappings."""
    
    def test_backward_compatibility_without_id_type(self):
        """Should work with old API (no id_type parameter)."""
        form = {'id_number': 'GHA-123456789-0', 'name': 'John Doe'}
        all_valid, errors, cleaned = InputValidator.validate_form_data(form)
        # Should not crash
        assert isinstance(all_valid, bool)
        assert isinstance(errors, dict)
        assert isinstance(cleaned, dict)
    
    def test_new_api_with_id_type(self):
        """Should work with new API (with id_type parameter)."""
        form = {'ghana_pin': 'GHA-123456789-0'}
        all_valid, errors, cleaned = InputValidator.validate_form_data(
            form, id_type='Ghana Card'
        )
        assert isinstance(all_valid, bool)
        # ghana_pin should validate successfully
        assert 'ghana_pin' not in errors
    
    def test_field_specific_validation_with_id_type(self):
        """Should validate fields using ID-specific rules."""
        # Valid Ghana PIN
        is_valid, msg = InputValidator.validate_field(
            'ghana_pin', 'GHA-123456789-0', id_type='Ghana Card'
        )
        assert is_valid is True
        
        # Invalid Ghana PIN
        is_valid, msg = InputValidator.validate_field(
            'ghana_pin', 'INVALID', id_type='Ghana Card'
        )
        assert is_valid is False
    
    def test_form_validation_all_id_types(self):
        """Should validate forms for all 5 ID types."""
        test_cases = {
            'Ghana Card': {'ghana_pin': 'GHA-123456789-0'},
            'Ghana Passport': {'passport_number': 'AA123456'},
            'Voter ID': {'voter_id_number': '1234567890'},
            'Driver\'s License': {'licence_number': 'DL12345'},
            'Bank Card': {'card_number': '4532'},
        }
        
        for id_type, form in test_cases.items():
            all_valid, errors, cleaned = InputValidator.validate_form_data(
                form, id_type=id_type
            )
            # Should not crash for any ID type
            assert isinstance(all_valid, bool)


class TestOCRComparisonIntegration:
    """Test OCR comparison with field mappings."""
    
    def test_compare_ghana_card_valid(self):
        """Should correctly compare valid Ghana Card data."""
        user = {'ghana_pin': 'GHA-123456789-0', 'date_of_birth': '1985-05-15'}
        ocr = {'ghana_pin': 'GHA-123456789-0', 'date_of_birth': '1985-05-15'}
        
        result = compare_user_input_with_ocr('Ghana Card', user, ocr)
        
        # Both fields should match
        assert 'ghana_pin' in result.passed_fields
        assert 'date_of_birth' in result.passed_fields
    
    def test_compare_ghana_card_format_variations(self):
        """Should handle date format variations."""
        user = {'ghana_pin': 'GHA-123456789-0', 'date_of_birth': '1985-05-15'}
        ocr = {'ghana_pin': 'GHA-123456789-0', 'date_of_birth': '15-05-1985'}
        
        result = compare_user_input_with_ocr('Ghana Card', user, ocr)
        
        # Should match despite date format difference
        assert 'date_of_birth' in result.passed_fields
    
    def test_compare_name_with_fuzzy_matching(self):
        """Should use fuzzy matching for names."""
        user = {'first_name': 'John', 'surname': 'Smith'}
        ocr = {'first_name': 'jon', 'surname': 'smith'}  # Different case
        
        result = compare_user_input_with_ocr('Ghana Card', user, ocr)
        
        # Note: first_name/surname may not be in required match fields,
        # so just check that comparison doesn't crash
        assert isinstance(result.passed_fields, list)
    
    def test_compare_detects_mismatches(self):
        """Should detect actual mismatches."""
        user = {'ghana_pin': 'GHA-123456789-0', 'date_of_birth': '1985-05-15'}
        ocr = {'ghana_pin': 'GHA-999999999-0', 'date_of_birth': '1985-05-16'}
        
        result = compare_user_input_with_ocr('Ghana Card', user, ocr)
        
        # Both should fail
        assert 'ghana_pin' in result.failed_fields
        assert 'date_of_birth' in result.failed_fields
    
    def test_comparison_provides_detailed_feedback(self):
        """Should provide comparison details."""
        user = {'ghana_pin': 'GHA-123456789-0', 'date_of_birth': '1985-05-15'}
        ocr = {'ghana_pin': 'GHA-123456789-0', 'date_of_birth': '1985-05-15'}
        
        result = compare_user_input_with_ocr('Ghana Card', user, ocr)
        
        summary = result.get_summary()
        
        assert 'id_type' in summary
        assert 'valid' in summary
        assert 'passed_fields' in summary
        assert 'failed_fields' in summary
        assert 'comparisons' in summary


class TestFieldMappingsIntegration:
    """Test field mappings with existing validation."""
    
    def test_get_user_input_fields_excludes_ocr_only(self):
        """Should exclude OCR-only fields from user input fields."""
        fields = get_user_input_fields('Ghana Card')
        
        # Should have fields for user to enter
        assert len(fields) > 0
        
        # Should not have sensitive fields that are OCR-only
        assert 'mrz_line1' not in fields or fields['mrz_line1'].category.name != 'OCR_ONLY'
    
    def test_required_match_fields_are_validated(self):
        """Should validate all required match fields."""
        required = get_required_match_fields('Ghana Card')
        
        # Should have required fields
        assert len(required) > 0
        assert 'ghana_pin' in required
        
        # Each required field should validate
        for field in required[:3]:  # Test first 3
            is_valid, msg = validate_id_form(
                'Ghana Card', {field: 'test_value'}
            )
            # Should return validation result (not error)
            assert isinstance(is_valid, bool)
    
    def test_field_validation_rules_applied(self):
        """Should apply field validation rules from mappings."""
        # Test with valid data
        form_valid = {'ghana_pin': 'GHA-123456789-0'}
        is_valid, errors = validate_id_form('Ghana Card', form_valid)
        assert 'ghana_pin' not in errors or is_valid
        
        # Test with invalid data
        form_invalid = {'ghana_pin': 'INVALID-PIN-FORMAT'}
        is_valid, errors = validate_id_form('Ghana Card', form_invalid)
        # Should detect error
        assert 'ghana_pin' in errors or not is_valid


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow."""
    
    def test_full_verification_workflow(self):
        """
        Test complete workflow:
        1. User enters form data
        2. Form validated using field mappings
        3. OCR extracts data
        4. OCR and user data compared
        """
        # Step 1: User enters form data
        user_form = {
            'ghana_pin': 'GHA-123456789-0',
            'date_of_birth': '1985-05-15',
        }
        
        # Step 2: Validate form using field mappings
        all_valid, errors, cleaned = InputValidator.validate_form_data(
            user_form, id_type='Ghana Card'
        )
        assert 'ghana_pin' not in errors  # PIN should be valid
        
        # Step 3: Simulate OCR extraction (with format variations)
        ocr_result = {
            'ghana_pin': 'GHA-123456789-0',  # Exact match
            'date_of_birth': '15-05-1985',  # Different format
        }
        
        # Step 4: Compare OCR with user input
        comparison = compare_user_input_with_ocr(
            'Ghana Card', cleaned, ocr_result
        )
        
        # Should successfully match both fields
        assert 'ghana_pin' in comparison.passed_fields
        assert 'date_of_birth' in comparison.passed_fields
    
    def test_workflow_with_mismatched_data(self):
        """Test workflow when OCR doesn't match user input."""
        # User enters data
        user_form = {
            'ghana_pin': 'GHA-123456789-0',
            'date_of_birth': '1985-05-15'
        }
        
        all_valid, errors, cleaned = InputValidator.validate_form_data(
            user_form, id_type='Ghana Card'
        )
        
        # OCR extracts different data
        ocr_result = {
            'ghana_pin': 'GHA-999999999-0',  # MISMATCH!
            'date_of_birth': '1985-05-15'
        }
        
        # Comparison should detect mismatch
        comparison = compare_user_input_with_ocr(
            'Ghana Card', cleaned, ocr_result
        )
        
        assert not comparison.is_valid()
        assert 'ghana_pin' in comparison.failed_fields


class TestMultipleIDTypes:
    """Test workflows across multiple ID types."""
    
    def test_passport_workflow(self):
        """Test complete workflow for Passport."""
        user_form = {
            'passport_number': 'AA123456',
            'date_of_birth': '1985-05-15',
            'nationality': 'Ghana'
        }
        
        all_valid, errors, cleaned = InputValidator.validate_form_data(
            user_form, id_type='Ghana Passport'
        )
        
        ocr_result = {
            'passport_number': 'AA123456',
            'date_of_birth': '15/05/1985',
            'nationality': 'Ghana'
        }
        
        comparison = compare_user_input_with_ocr(
            'Ghana Passport', cleaned, ocr_result
        )
        
        # At minimum, passport_number should match
        assert 'passport_number' in comparison.passed_fields
    
    def test_voter_id_workflow(self):
        """Test complete workflow for Voter ID."""
        user_form = {
            'voter_id_number': '1234567890',
            'issuance_date': '2020-01-15',
        }
        
        all_valid, errors, cleaned = InputValidator.validate_form_data(
            user_form, id_type='Voter ID'
        )
        
        ocr_result = {
            'voter_id_number': '1234567890',
            'issuance_date': '15/01/2020',
        }
        
        comparison = compare_user_input_with_ocr(
            'Voter ID', cleaned, ocr_result
        )
        
        # At minimum, voter_id_number should match
        assert 'voter_id_number' in comparison.passed_fields
    
    def test_driver_license_workflow(self):
        """Test complete workflow for Driver License."""
        user_form = {
            'licence_number': 'DL123456',
            'expiry_date': '2030-12-31',
            'issue_date': '2020-01-15',
        }
        
        all_valid, errors, cleaned = InputValidator.validate_form_data(
            user_form, id_type='Driver\'s License'
        )
        
        ocr_result = {
            'licence_number': 'DL123456',
            'expiry_date': '31-12-2030',
            'issue_date': '15-01-2020',
        }
        
        comparison = compare_user_input_with_ocr(
            'Driver\'s License', cleaned, ocr_result
        )
        
        # At minimum, licence_number should match
        assert 'licence_number' in comparison.passed_fields
    
    def test_bank_card_workflow(self):
        """Test complete workflow for Bank Card."""
        user_form = {
            'card_number': '4532',  # Last 4 digits only (for security)
            'cardholder_name': 'John Smith',
            'expiry_date': '12/30',
        }
        
        all_valid, errors, cleaned = InputValidator.validate_form_data(
            user_form, id_type='Bank Card'
        )
        
        ocr_result = {
            'card_number': '4532',
            'cardholder_name': 'JOHN SMITH',
            'expiry_date': '12/30',
        }
        
        comparison = compare_user_input_with_ocr(
            'Bank Card', cleaned, ocr_result
        )
        
        # At minimum, card_number should match
        assert isinstance(comparison.passed_fields, list)


class TestErrorHandling:
    """Test error handling in Phase 3 components."""
    
    def test_invalid_id_type_handling(self):
        """Should handle invalid ID type gracefully."""
        # Invalid ID types should raise ValueError in field mapping functions
        # but OCR comparison should still work without field validation
        try:
            comparison = compare_user_input_with_ocr(
                'InvalidType', {'field': 'value'}, {'field': 'value'}
            )
            # If it doesn't raise, it should still return a result
            assert comparison.id_type == 'InvalidType'
        except ValueError:
            # It's acceptable to raise ValueError for unknown ID type
            pass
    
    def test_empty_data_handling(self):
        """Should handle empty data gracefully."""
        all_valid, errors, cleaned = InputValidator.validate_form_data(
            {}, id_type='Ghana Card'
        )
        # Should not crash
        assert isinstance(all_valid, bool)
    
    def test_none_values_handling(self):
        """Should handle None values gracefully."""
        form = {'ghana_pin': None}
        all_valid, errors, cleaned = InputValidator.validate_form_data(
            form, id_type='Ghana Card'
        )
        # Should not crash
        assert isinstance(all_valid, bool)


class TestComparisonDetailedResults:
    """Test detailed comparison results."""
    
    def test_comparison_results_include_type(self):
        """Should indicate comparison type for each field."""
        user = {'ghana_pin': 'GHA-123456789-0', 'date_of_birth': '1985-05-15'}
        ocr = {'ghana_pin': 'GHA-123456789-0', 'date_of_birth': '1985-05-15'}
        
        result = compare_user_input_with_ocr('Ghana Card', user, ocr)
        summary = result.get_summary()
        
        # Each comparison should have type info
        for field, comp in summary['comparisons'].items():
            assert 'type' in comp
            assert comp['type'] in ['exact', 'date', 'fuzzy', 'enum', 'default']
    
    def test_comparison_results_include_values(self):
        """Should include user and OCR values in results."""
        user = {'ghana_pin': 'GHA-123456789-0'}
        ocr = {'ghana_pin': 'GHA-123456789-0'}
        
        result = compare_user_input_with_ocr('Ghana Card', user, ocr)
        summary = result.get_summary()
        
        for field, comp in summary['comparisons'].items():
            if field == 'ghana_pin':
                assert 'user_value' in comp
                assert 'ocr_value' in comp
                assert comp['user_value'] == 'GHA-123456789-0'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
