"""
OCR vs User Input Comparison
Compares extracted OCR data with user-entered data to detect discrepancies.
"""

from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher
import re
from logger_config import audit_logger
from id_field_mappings import (
    get_required_match_fields, get_id_type_fields,
    ID_TYPE_REGISTRY
)


class FieldComparator:
    """Compares OCR-extracted fields with user-entered fields."""
    
    # Fuzzy matching threshold (0-1, higher = stricter)
    FUZZY_MATCH_THRESHOLD = 0.85
    
    # Field comparison rules
    COMPARISON_RULES = {
        'exact': ['ghana_pin', 'voter_id_number', 'passport_number', 'licence_number'],
        'date': ['date_of_birth', 'expiry_date', 'issue_date', 'issuance_date'],
        'fuzzy': ['full_name', 'surname', 'firstname', 'cardholder_name'],
        'enum': ['sex', 'gender', 'licence_class'],
    }
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for comparison: lowercase, remove extra spaces."""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip().lower())
    
    @staticmethod
    def normalize_date(date_str: str) -> str:
        """Normalize date to YYYY-MM-DD format."""
        if not date_str:
            return ""
        
        # Try common date formats
        formats = [
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y/%m/%d',
            '%d.%m.%Y',
        ]
        
        for fmt in formats:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_str.strip(), fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Return as-is if no format matches
        return date_str.strip()
    
    @staticmethod
    def fuzzy_match(str1: str, str2: str, threshold: float = 0.85) -> Tuple[bool, float]:
        """
        Fuzzy string matching using sequence ratio.
        Returns (match, similarity_score)
        """
        if not str1 or not str2:
            return False, 0.0
        
        norm1 = FieldComparator.normalize_text(str1)
        norm2 = FieldComparator.normalize_text(str2)
        
        if norm1 == norm2:
            return True, 1.0
        
        ratio = SequenceMatcher(None, norm1, norm2).ratio()
        return ratio >= threshold, ratio
    
    @staticmethod
    def compare_exact(user_value: str, ocr_value: str) -> Tuple[bool, str]:
        """Exact match comparison."""
        if not user_value or not ocr_value:
            return False, "Missing value"
        
        if user_value.strip().upper() == ocr_value.strip().upper():
            return True, "Exact match"
        
        return False, f"Mismatch: '{user_value}' vs '{ocr_value}'"
    
    @staticmethod
    def compare_date(user_value: str, ocr_value: str) -> Tuple[bool, str]:
        """Date comparison with format normalization."""
        if not user_value or not ocr_value:
            return False, "Missing value"
        
        user_norm = FieldComparator.normalize_date(user_value)
        ocr_norm = FieldComparator.normalize_date(ocr_value)
        
        if user_norm == ocr_norm:
            return True, "Date match"
        
        return False, f"Date mismatch: '{user_norm}' vs '{ocr_norm}'"
    
    @staticmethod
    def compare_fuzzy(user_value: str, ocr_value: str, threshold: float = 0.85) -> Tuple[bool, str]:
        """Fuzzy string matching."""
        if not user_value or not ocr_value:
            return False, "Missing value"
        
        match, score = FieldComparator.fuzzy_match(user_value, ocr_value, threshold)
        
        if match:
            return True, f"Fuzzy match ({score:.0%})"
        
        return False, f"No match: '{user_value}' vs '{ocr_value}' ({score:.0%})"
    
    @staticmethod
    def compare_enum(user_value: str, ocr_value: str, enum_values: List[str] = None) -> Tuple[bool, str]:
        """Enum field comparison (sex, gender, class, etc)."""
        if not user_value or not ocr_value:
            return False, "Missing value"
        
        # Normalize to single character for gender/sex fields
        user_norm = user_value.strip().upper()[0] if user_value else ""
        ocr_norm = ocr_value.strip().upper()[0] if ocr_value else ""
        
        if user_norm == ocr_norm:
            return True, f"Enum match: {user_norm}"
        
        return False, f"Enum mismatch: '{user_norm}' vs '{ocr_norm}'"
    
    @classmethod
    def compare_field(
        cls,
        field_name: str,
        user_value: str,
        ocr_value: str
    ) -> Tuple[bool, str, str]:
        """
        Compare a single field between user input and OCR.
        Returns (match, message, comparison_type)
        """
        if field_name in cls.COMPARISON_RULES['exact']:
            match, msg = cls.compare_exact(user_value, ocr_value)
            return match, msg, 'exact'
        
        elif field_name in cls.COMPARISON_RULES['date']:
            match, msg = cls.compare_date(user_value, ocr_value)
            return match, msg, 'date'
        
        elif field_name in cls.COMPARISON_RULES['fuzzy']:
            match, msg = cls.compare_fuzzy(user_value, ocr_value, cls.FUZZY_MATCH_THRESHOLD)
            return match, msg, 'fuzzy'
        
        elif field_name in cls.COMPARISON_RULES['enum']:
            match, msg = cls.compare_enum(user_value, ocr_value)
            return match, msg, 'enum'
        
        # Default: exact match
        match, msg = cls.compare_exact(user_value, ocr_value)
        return match, msg, 'default'


class VerificationResult:
    """Result of comparing user input with OCR extraction."""
    
    def __init__(self, id_type: str):
        self.id_type = id_type
        self.field_comparisons: Dict[str, Dict] = {}
        self.passed_fields = []
        self.failed_fields = []
        self.missing_fields = []
    
    def add_comparison(
        self,
        field_name: str,
        user_value: str,
        ocr_value: str,
        match: bool,
        message: str,
        comparison_type: str
    ):
        """Add a field comparison result."""
        self.field_comparisons[field_name] = {
            'user_value': user_value,
            'ocr_value': ocr_value,
            'match': match,
            'message': message,
            'type': comparison_type
        }
        
        if not user_value or not ocr_value:
            self.missing_fields.append(field_name)
        elif match:
            self.passed_fields.append(field_name)
        else:
            self.failed_fields.append(field_name)
    
    def is_valid(self) -> bool:
        """Overall validation: all required matches must pass."""
        required_fields = get_required_match_fields(self.id_type)
        for field in required_fields:
            if field in self.failed_fields or field in self.missing_fields:
                return False
        return True
    
    def get_summary(self) -> Dict:
        """Get summary of verification result."""
        return {
            'id_type': self.id_type,
            'valid': self.is_valid(),
            'passed_count': len(self.passed_fields),
            'failed_count': len(self.failed_fields),
            'missing_count': len(self.missing_fields),
            'passed_fields': self.passed_fields,
            'failed_fields': self.failed_fields,
            'missing_fields': self.missing_fields,
            'comparisons': self.field_comparisons
        }


def compare_user_input_with_ocr(
    id_type: str,
    user_data: Dict[str, str],
    ocr_data: Dict[str, str]
) -> VerificationResult:
    """
    Compare user-entered data with OCR-extracted data.
    
    Args:
        id_type: Type of ID (e.g., 'Ghana Card')
        user_data: User-entered field values
        ocr_data: OCR-extracted field values
    
    Returns:
        VerificationResult with comparison details
    """
    result = VerificationResult(id_type)
    
    # Get required match fields for this ID type
    required_fields = get_required_match_fields(id_type)
    
    audit_logger.logger.info('Starting OCR vs user input comparison', extra={
        'event': 'ocr_comparison_start',
        'id_type': id_type,
        'required_fields': required_fields
    })
    
    # Compare each required field
    for field_name in required_fields:
        user_value = user_data.get(field_name, '')
        ocr_value = ocr_data.get(field_name, '')
        
        match, message, comp_type = FieldComparator.compare_field(
            field_name, user_value, ocr_value
        )
        
        result.add_comparison(
            field_name, user_value, ocr_value, match, message, comp_type
        )
        
        audit_logger.logger.debug(
            f'Field comparison: {field_name}',
            extra={
                'event': 'field_comparison',
                'field': field_name,
                'match': match,
                'comp_type': comp_type,  # Renamed from 'type' to avoid conflict
                'user_value': user_value[:20] if user_value else '',  # Truncate for logging
                'ocr_value': ocr_value[:20] if ocr_value else '',
                'result_message': message  # Renamed from 'message' to avoid logging conflict
            }
        )
    
    # Log overall result
    summary = result.get_summary()
    audit_logger.logger.info('OCR vs user input comparison complete', extra={
        'event': 'ocr_comparison_complete',
        'id_type': id_type,
        'valid': result.is_valid(),
        'summary': summary
    })
    
    return result


if __name__ == '__main__':
    # Example usage
    print("=== OCR vs User Input Comparison Example ===\n")
    
    # Test data
    user_data = {
        'ghana_pin': 'GHA-123456789-0',
        'date_of_birth': '1985-05-15',
        'expiry_date': '2030-12-31',
        'sex': 'M',
        'full_name': 'Kwame Kofi'
    }
    
    ocr_data = {
        'ghana_pin': 'GHA-123456789-0',
        'date_of_birth': '1985-05-15',
        'expiry_date': '2030-12-31',
        'sex': 'Male',  # Different format
        'full_name': 'KWAME  KOFI'  # Extra space
    }
    
    result = compare_user_input_with_ocr('Ghana Card', user_data, ocr_data)
    summary = result.get_summary()
    
    print(f"ID Type: {summary['id_type']}")
    print(f"Valid: {summary['valid']}")
    print(f"Passed: {summary['passed_count']}")
    print(f"Failed: {summary['failed_count']}")
    print(f"\nComparisons:")
    for field, comp in summary['comparisons'].items():
        print(f"  {field}: {comp['message']} ({comp['type']})")
