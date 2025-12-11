"""
Unit tests for OCR comparison functionality.
Tests FieldComparator, VerificationResult, and compare_user_input_with_ocr.
"""

import pytest
from datetime import datetime, timedelta
from ocr_comparison import (
    FieldComparator, VerificationResult, compare_user_input_with_ocr
)


class TestFieldComparatorNormalization:
    """Test text and date normalization."""
    
    def test_normalize_text_lowercase(self):
        """Should convert text to lowercase."""
        assert FieldComparator.normalize_text("HELLO") == "hello"
        assert FieldComparator.normalize_text("HeLLo") == "hello"
    
    def test_normalize_text_whitespace(self):
        """Should remove extra whitespace."""
        assert FieldComparator.normalize_text("  hello  ") == "hello"
        assert FieldComparator.normalize_text("hello   world") == "hello world"
    
    def test_normalize_text_empty(self):
        """Should handle empty strings."""
        assert FieldComparator.normalize_text("") == ""
        assert FieldComparator.normalize_text(None) == ""
    
    def test_normalize_date_iso_format(self):
        """Should recognize ISO format YYYY-MM-DD."""
        assert FieldComparator.normalize_date("2020-05-15") == "2020-05-15"
    
    def test_normalize_date_dd_mm_yyyy(self):
        """Should convert DD-MM-YYYY to YYYY-MM-DD."""
        assert FieldComparator.normalize_date("15-05-2020") == "2020-05-15"
    
    def test_normalize_date_dd_slash_mm_slash_yyyy(self):
        """Should convert DD/MM/YYYY to YYYY-MM-DD."""
        assert FieldComparator.normalize_date("15/05/2020") == "2020-05-15"
    
    def test_normalize_date_dot_format(self):
        """Should convert DD.MM.YYYY to YYYY-MM-DD."""
        assert FieldComparator.normalize_date("15.05.2020") == "2020-05-15"
    
    def test_normalize_date_empty(self):
        """Should handle empty dates."""
        assert FieldComparator.normalize_date("") == ""
        assert FieldComparator.normalize_date(None) == ""


class TestFieldComparatorFuzzyMatch:
    """Test fuzzy string matching."""
    
    def test_exact_match(self):
        """Should detect exact matches."""
        match, score = FieldComparator.fuzzy_match("Kwame Kofi", "KWAME KOFI")
        assert match is True
        assert score == 1.0
    
    def test_high_similarity(self):
        """Should detect high similarity (>85%)."""
        match, score = FieldComparator.fuzzy_match("John Smith", "John Smth")
        assert match is True
        assert score >= 0.85
    
    def test_low_similarity(self):
        """Should reject low similarity (<85%)."""
        match, score = FieldComparator.fuzzy_match("John Smith", "Jane Doe")
        assert match is False
    
    def test_whitespace_handling(self):
        """Should normalize whitespace before matching."""
        match, score = FieldComparator.fuzzy_match("John  Smith", "john smith")
        assert match is True
    
    def test_custom_threshold(self):
        """Should respect custom similarity threshold."""
        match, score = FieldComparator.fuzzy_match(
            "John Smith", "John Smth", threshold=0.75
        )
        assert match is True
        
        match, score = FieldComparator.fuzzy_match(
            "John Smith", "John Smth", threshold=0.95
        )
        assert match is False


class TestFieldComparatorExactMatch:
    """Test exact field matching."""
    
    def test_exact_match_success(self):
        """Should match identical values."""
        match, msg = FieldComparator.compare_exact("GHA-123456789-0", "GHA-123456789-0")
        assert match is True
        assert "match" in msg.lower()
    
    def test_exact_match_case_insensitive(self):
        """Should be case-insensitive."""
        match, msg = FieldComparator.compare_exact(
            "GHA-123456789-0", "gha-123456789-0"
        )
        assert match is True
    
    def test_exact_match_failure(self):
        """Should detect mismatches."""
        match, msg = FieldComparator.compare_exact(
            "GHA-123456789-0", "GHA-999999999-0"
        )
        assert match is False
        assert "mismatch" in msg.lower()
    
    def test_exact_match_empty_values(self):
        """Should handle empty values."""
        match, msg = FieldComparator.compare_exact("", "GHA-123456789-0")
        assert match is False
        assert "missing" in msg.lower()
        
        match, msg = FieldComparator.compare_exact("GHA-123456789-0", "")
        assert match is False


class TestFieldComparatorDateMatch:
    """Test date field matching."""
    
    def test_date_match_same_format(self):
        """Should match dates in same format."""
        match, msg = FieldComparator.compare_date("1985-05-15", "1985-05-15")
        assert match is True
    
    def test_date_match_different_formats(self):
        """Should match dates in different formats."""
        match, msg = FieldComparator.compare_date("1985-05-15", "15-05-1985")
        assert match is True
    
    def test_date_match_failure(self):
        """Should detect date mismatches."""
        match, msg = FieldComparator.compare_date("1985-05-15", "1985-05-16")
        assert match is False
    
    def test_date_match_empty_values(self):
        """Should handle empty dates."""
        match, msg = FieldComparator.compare_date("", "1985-05-15")
        assert match is False


class TestFieldComparatorFuzzyCompare:
    """Test fuzzy comparison method."""
    
    def test_fuzzy_exact_match(self):
        """Should detect exact name matches."""
        match, msg = FieldComparator.compare_fuzzy("John Smith", "JOHN SMITH")
        assert match is True
    
    def test_fuzzy_close_match(self):
        """Should detect close name matches."""
        match, msg = FieldComparator.compare_fuzzy("John Smith", "Jon Smith")
        assert match is True
    
    def test_fuzzy_no_match(self):
        """Should reject dissimilar names."""
        match, msg = FieldComparator.compare_fuzzy("John Smith", "Jane Doe")
        assert match is False
    
    def test_fuzzy_custom_threshold(self):
        """Should respect custom fuzzy threshold."""
        match, msg = FieldComparator.compare_fuzzy(
            "John Smith", "Jon Smith", threshold=0.95
        )
        assert match is False


class TestFieldComparatorEnumCompare:
    """Test enum field comparison."""
    
    def test_enum_match_M_F(self):
        """Should match gender/sex fields."""
        match, msg = FieldComparator.compare_enum("M", "M")
        assert match is True
        
        match, msg = FieldComparator.compare_enum("M", "Male")
        assert match is True
    
    def test_enum_mismatch(self):
        """Should detect gender mismatches."""
        match, msg = FieldComparator.compare_enum("M", "F")
        assert match is False
    
    def test_enum_case_insensitive(self):
        """Should be case-insensitive."""
        match, msg = FieldComparator.compare_enum("male", "M")
        assert match is True


class TestFieldComparatorCompareField:
    """Test field comparison routing."""
    
    def test_exact_field_ghana_pin(self):
        """Should use exact comparison for ghana_pin."""
        match, msg, comp_type = FieldComparator.compare_field(
            'ghana_pin', 'GHA-123456789-0', 'GHA-123456789-0'
        )
        assert match is True
        assert comp_type == 'exact'
    
    def test_date_field_date_of_birth(self):
        """Should use date comparison for date_of_birth."""
        match, msg, comp_type = FieldComparator.compare_field(
            'date_of_birth', '1985-05-15', '15-05-1985'
        )
        assert match is True
        assert comp_type == 'date'
    
    def test_fuzzy_field_full_name(self):
        """Should use fuzzy comparison for full_name."""
        match, msg, comp_type = FieldComparator.compare_field(
            'full_name', 'John Smith', 'jon smith'
        )
        assert match is True
        assert comp_type == 'fuzzy'
    
    def test_enum_field_sex(self):
        """Should use enum comparison for sex."""
        match, msg, comp_type = FieldComparator.compare_field(
            'sex', 'M', 'Male'
        )
        assert match is True
        assert comp_type == 'enum'


class TestVerificationResult:
    """Test VerificationResult class."""
    
    def test_init(self):
        """Should initialize correctly."""
        result = VerificationResult('Ghana Card')
        assert result.id_type == 'Ghana Card'
        assert result.passed_fields == []
        assert result.failed_fields == []
        assert result.missing_fields == []
    
    def test_add_passed_comparison(self):
        """Should track passed comparisons."""
        result = VerificationResult('Ghana Card')
        result.add_comparison(
            'ghana_pin', 'GHA-123456789-0', 'GHA-123456789-0',
            True, 'Exact match', 'exact'
        )
        assert 'ghana_pin' in result.passed_fields
        assert len(result.passed_fields) == 1
    
    def test_add_failed_comparison(self):
        """Should track failed comparisons."""
        result = VerificationResult('Ghana Card')
        result.add_comparison(
            'ghana_pin', 'GHA-123456789-0', 'GHA-999999999-0',
            False, 'Mismatch', 'exact'
        )
        assert 'ghana_pin' in result.failed_fields
        assert len(result.failed_fields) == 1
    
    def test_add_missing_value(self):
        """Should track missing values."""
        result = VerificationResult('Ghana Card')
        result.add_comparison(
            'ghana_pin', '', 'GHA-123456789-0',
            False, 'Missing value', 'exact'
        )
        assert 'ghana_pin' in result.missing_fields
    
    def test_is_valid_all_pass(self):
        """Should be valid when all required fields match."""
        result = VerificationResult('Ghana Card')
        result.add_comparison(
            'ghana_pin', 'GHA-123456789-0', 'GHA-123456789-0',
            True, 'Match', 'exact'
        )
        result.add_comparison(
            'date_of_birth', '1985-05-15', '1985-05-15',
            True, 'Match', 'date'
        )
        assert result.is_valid() is True
    
    def test_is_valid_required_fail(self):
        """Should be invalid when required field fails."""
        result = VerificationResult('Ghana Card')
        result.add_comparison(
            'ghana_pin', 'GHA-123456789-0', 'GHA-999999999-0',
            False, 'Mismatch', 'exact'
        )
        # Required field failed
        assert result.is_valid() is False
    
    def test_get_summary(self):
        """Should provide accurate summary."""
        result = VerificationResult('Ghana Card')
        result.add_comparison(
            'ghana_pin', 'GHA-123456789-0', 'GHA-123456789-0',
            True, 'Match', 'exact'
        )
        result.add_comparison(
            'date_of_birth', '1985-05-15', '1985-05-16',
            False, 'Mismatch', 'date'
        )
        
        summary = result.get_summary()
        assert summary['id_type'] == 'Ghana Card'
        assert summary['passed_count'] >= 1
        assert summary['failed_count'] >= 1


class TestCompareUserInputWithOCR:
    """Test the main compare_user_input_with_ocr function."""
    
    def test_valid_ghana_card_comparison(self):
        """Should correctly compare valid Ghana Card data."""
        user_data = {
            'ghana_pin': 'GHA-123456789-0',
            'date_of_birth': '1985-05-15',
            'expiry_date': '2030-12-31',
            'sex': 'M',
        }
        
        ocr_data = {
            'ghana_pin': 'GHA-123456789-0',
            'date_of_birth': '1985-05-15',
            'expiry_date': '2030-12-31',
            'sex': 'Male',
        }
        
        result = compare_user_input_with_ocr('Ghana Card', user_data, ocr_data)
        assert result.is_valid() is True
    
    def test_ghana_card_with_mismatches(self):
        """Should detect mismatches in Ghana Card data."""
        user_data = {
            'ghana_pin': 'GHA-123456789-0',
            'date_of_birth': '1985-05-15',
        }
        
        ocr_data = {
            'ghana_pin': 'GHA-999999999-0',  # Mismatch
            'date_of_birth': '1985-05-15',
        }
        
        result = compare_user_input_with_ocr('Ghana Card', user_data, ocr_data)
        assert 'ghana_pin' in result.failed_fields
    
    def test_comparison_with_name_variations(self):
        """Should handle name variations gracefully."""
        user_data = {
            'full_name': 'John Smith',
        }
        
        ocr_data = {
            'full_name': 'jon smith',  # Case and spelling variation
        }
        
        result = compare_user_input_with_ocr('Ghana Card', user_data, ocr_data)
        # Should match with fuzzy matching
        assert result.is_valid()
    
    def test_comparison_with_format_variations(self):
        """Should handle format variations in dates."""
        user_data = {
            'date_of_birth': '1985-05-15',
        }
        
        ocr_data = {
            'date_of_birth': '15/05/1985',  # Different format
        }
        
        result = compare_user_input_with_ocr('Ghana Card', user_data, ocr_data)
        # Should match after normalization
        assert result.is_valid()
    
    def test_invalid_id_type(self):
        """Should handle invalid ID type gracefully."""
        user_data = {'field': 'value'}
        ocr_data = {'field': 'value'}
        
        # Should not crash with invalid ID type
        result = compare_user_input_with_ocr('InvalidType', user_data, ocr_data)
        assert result.id_type == 'InvalidType'
    
    def test_empty_data(self):
        """Should handle empty data."""
        result = compare_user_input_with_ocr('Ghana Card', {}, {})
        # Should report missing fields
        assert len(result.missing_fields) > 0
    
    def test_partial_data(self):
        """Should handle partial data."""
        user_data = {
            'ghana_pin': 'GHA-123456789-0',
        }
        
        ocr_data = {
            'ghana_pin': 'GHA-123456789-0',
        }
        
        result = compare_user_input_with_ocr('Ghana Card', user_data, ocr_data)
        # PIN matches but other required fields missing
        assert 'ghana_pin' in result.passed_fields


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_normalize_special_characters(self):
        """Should handle special characters in names."""
        assert FieldComparator.normalize_text("O'Brien") == "o'brien"
        assert FieldComparator.normalize_text("Jean-Paul") == "jean-paul"
    
    def test_normalize_unicode(self):
        """Should handle Unicode characters."""
        normalized = FieldComparator.normalize_text("Café")
        assert normalized == "café"
    
    def test_date_normalization_with_spaces(self):
        """Should handle dates with extra spaces."""
        result = FieldComparator.normalize_date("  2020-05-15  ")
        assert result == "2020-05-15"
    
    def test_very_long_strings(self):
        """Should handle very long strings."""
        long_name = "A" * 1000
        normalized = FieldComparator.normalize_text(long_name)
        assert normalized == long_name.lower()
    
    def test_special_date_formats(self):
        """Should handle various date formats."""
        formats = [
            ("2020-05-15", "2020-05-15"),
            ("15-05-2020", "2020-05-15"),
            ("15/05/2020", "2020-05-15"),
            ("2020/05/15", "2020-05-15"),
            ("15.05.2020", "2020-05-15"),
        ]
        
        for input_date, expected in formats:
            result = FieldComparator.normalize_date(input_date)
            assert result == expected


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
