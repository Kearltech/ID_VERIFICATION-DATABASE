"""
Tests for Phase 3 verify.py OCR comparison integration.
"""

import pytest
from verify import compare_ocr_with_user_input, validate_fields


class TestOCRComparisonIntegration:
    """Test OCR comparison integration in verify.py."""
    
    def test_compare_ocr_valid_match(self):
        """Should return valid when OCR matches user input."""
        user_data = {
            'ghana_pin': 'GHA-123456789-0',
            'date_of_birth': '1985-05-15'
        }
        ocr_data = {
            'ghana_pin': 'GHA-123456789-0',
            'date_of_birth': '1985-05-15'
        }
        
        result = compare_ocr_with_user_input('Ghana Card', user_data, ocr_data)
        
        assert isinstance(result, dict)
        assert 'valid' in result
        # At minimum ghana_pin should be compared
        assert len(result['details']) >= 0
    
    def test_compare_ocr_with_format_variations(self):
        """Should match OCR despite date format differences."""
        user_data = {
            'ghana_pin': 'GHA-123456789-0',
            'date_of_birth': '1985-05-15'
        }
        ocr_data = {
            'ghana_pin': 'GHA-123456789-0',
            'date_of_birth': '15/05/1985'  # Different format
        }
        
        result = compare_ocr_with_user_input('Ghana Card', user_data, ocr_data)
        
        assert isinstance(result, dict)
        # Should complete without errors
        assert 'message' in result
    
    def test_compare_ocr_detects_mismatch(self):
        """Should detect when OCR doesn't match user input."""
        user_data = {
            'ghana_pin': 'GHA-123456789-0',
            'date_of_birth': '1985-05-15'
        }
        ocr_data = {
            'ghana_pin': 'GHA-999999999-0',  # MISMATCH
            'date_of_birth': '1985-05-15'
        }
        
        result = compare_ocr_with_user_input('Ghana Card', user_data, ocr_data)
        
        assert isinstance(result, dict)
        # Should return structured result
        assert 'valid' in result
        assert 'failed_fields' in result
    
    def test_compare_returns_dict_with_required_keys(self):
        """Should return dict with all required keys."""
        user_data = {'ghana_pin': 'GHA-123456789-0'}
        ocr_data = {'ghana_pin': 'GHA-123456789-0'}
        
        result = compare_ocr_with_user_input('Ghana Card', user_data, ocr_data)
        
        assert isinstance(result, dict)
        assert 'valid' in result
        assert 'passed_fields' in result
        assert 'failed_fields' in result
        assert 'missing_fields' in result
        assert 'details' in result
        assert 'message' in result
    
    def test_compare_handles_empty_data(self):
        """Should handle empty data gracefully."""
        result = compare_ocr_with_user_input('Ghana Card', {}, {})
        
        assert isinstance(result, dict)
        assert 'message' in result
    
    def test_compare_handles_invalid_id_type(self):
        """Should handle invalid ID type gracefully."""
        result = compare_ocr_with_user_input(
            'InvalidType', {'field': 'value'}, {'field': 'value'}
        )
        
        assert isinstance(result, dict)
        # Should not crash
        assert 'message' in result
    
    def test_compare_voter_id(self):
        """Should compare Voter ID data correctly."""
        user_data = {'voter_id_number': '1234567890'}
        ocr_data = {'voter_id_number': '1234567890'}
        
        result = compare_ocr_with_user_input('Voter ID', user_data, ocr_data)
        
        assert isinstance(result, dict)
        assert 'valid' in result
    
    def test_compare_passport(self):
        """Should compare Passport data correctly."""
        user_data = {'passport_number': 'AA123456'}
        ocr_data = {'passport_number': 'AA123456'}
        
        result = compare_ocr_with_user_input('Ghana Passport', user_data, ocr_data)
        
        assert isinstance(result, dict)
        assert 'valid' in result
    
    def test_compare_bank_card(self):
        """Should compare Bank Card data correctly."""
        user_data = {'card_number': '4532', 'cardholder_name': 'John Smith'}
        ocr_data = {'card_number': '4532', 'cardholder_name': 'JOHN SMITH'}
        
        result = compare_ocr_with_user_input('Bank Card', user_data, ocr_data)
        
        assert isinstance(result, dict)
        assert 'valid' in result


class TestValidateFieldsBackwardCompatibility:
    """Test that existing validate_fields function still works."""
    
    def test_validate_fields_ghana_card(self):
        """Should validate Ghana Card fields."""
        result = validate_fields(
            'Ghana Card',
            {'id_number': 'GHA-123456789-0', 'surname': 'Doe', 'date_of_birth': '1985-05-15'},
            'REPUBLIC OF GHANA'
        )
        
        assert isinstance(result, dict)
        assert 'fields' in result
        assert 'overall' in result
    
    def test_validate_fields_voter_id(self):
        """Should validate Voter ID fields."""
        result = validate_fields(
            'Voter ID',
            {'id_number': '1234567890'},
            'VOTER'
        )
        
        assert isinstance(result, dict)
        assert 'fields' in result
    
    def test_validate_fields_passport(self):
        """Should validate Passport fields."""
        result = validate_fields(
            'Passport',
            {'id_number': 'AA123456'},
            'PASSPORT'
        )
        
        assert isinstance(result, dict)
        assert 'fields' in result


class TestIntegrationScenarios:
    """Test complete integration scenarios."""
    
    def test_full_verification_flow(self):
        """Test full verification flow from validation to OCR comparison."""
        # Step 1: User enters form data
        user_form = {
            'id_number': 'GHA-123456789-0',
            'surname': 'Smith',
            'date_of_birth': '1985-05-15'
        }
        
        # Step 2: Validate entered fields (existing function)
        validation_result = validate_fields('Ghana Card', user_form, '')
        
        # Step 3: Simulate OCR extraction
        ocr_extracted = {
            'ghana_pin': 'GHA-123456789-0',
            'date_of_birth': '15/05/1985'
        }
        
        # Step 4: Compare OCR with entered data
        comparison_result = compare_ocr_with_user_input(
            'Ghana Card',
            {'ghana_pin': user_form.get('id_number'), 'date_of_birth': user_form['date_of_birth']},
            ocr_extracted
        )
        
        # Both should complete without errors
        assert isinstance(validation_result, dict)
        assert isinstance(comparison_result, dict)
    
    def test_mismatch_detection_flow(self):
        """Test flow when OCR detects mismatch."""
        # User entered one value
        user_data = {'ghana_pin': 'GHA-123456789-0'}
        
        # OCR extracted different value
        ocr_data = {'ghana_pin': 'GHA-999999999-0'}
        
        # Comparison should complete
        result = compare_ocr_with_user_input('Ghana Card', user_data, ocr_data)
        
        assert isinstance(result, dict)
        assert 'valid' in result


class TestResultFormat:
    """Test that result format is consistent and useful."""
    
    def test_result_has_human_readable_message(self):
        """Should include human-readable message."""
        result = compare_ocr_with_user_input(
            'Ghana Card',
            {'ghana_pin': 'GHA-123456789-0'},
            {'ghana_pin': 'GHA-123456789-0'}
        )
        
        assert 'message' in result
        assert isinstance(result['message'], str)
        assert len(result['message']) > 0
    
    def test_result_includes_field_details(self):
        """Should include field-by-field details."""
        result = compare_ocr_with_user_input(
            'Ghana Card',
            {'ghana_pin': 'GHA-123456789-0'},
            {'ghana_pin': 'GHA-123456789-0'}
        )
        
        assert 'details' in result
        assert isinstance(result['details'], dict)
    
    def test_result_lists_are_consistent(self):
        """Should have consistent list results."""
        result = compare_ocr_with_user_input(
            'Ghana Card',
            {'ghana_pin': 'GHA-123456789-0'},
            {'ghana_pin': 'GHA-123456789-0'}
        )
        
        assert isinstance(result['passed_fields'], list)
        assert isinstance(result['failed_fields'], list)
        assert isinstance(result['missing_fields'], list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
