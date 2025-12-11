"""
Input validation and sanitization for the ID Verification system.
Ensures all user inputs are safe and conform to expected formats.
"""

import re
from typing import Dict, Tuple, Optional, Any
from datetime import datetime
from exceptions import ValidationError, create_error
from id_field_mappings import (
    validate_id_field as field_mapping_validate,
    validate_id_form as field_mapping_validate_form,
    get_id_type_fields,
    ID_TYPE_REGISTRY
)


class InputValidator:
    """Centralized input validation with security checks."""
    
    # Fallback validation rules for fields not in ID type registry
    FALLBACK_RULES = {
        'id_number': {
            'max_length': 50,
            'pattern': r'^[A-Z0-9\-]{5,50}$',
            'description': 'Alphanumeric, 5-50 chars, hyphens allowed',
            'type': str
        },
        'name': {
            'max_length': 100,
            'pattern': r"^[a-zA-Z\s\-']{2,100}$",
            'description': "Letters, spaces, hyphens, apostrophes only (2-100 chars)",
            'type': str
        },
        'surname': {
            'max_length': 100,
            'pattern': r"^[a-zA-Z\s\-']{2,100}$",
            'description': "Letters, spaces, hyphens, apostrophes only (2-100 chars)",
            'type': str
        },
        'firstname': {
            'max_length': 100,
            'pattern': r"^[a-zA-Z\s\-']{2,100}$",
            'description': "Letters, spaces, hyphens, apostrophes only (2-100 chars)",
            'type': str
        },
        'date_of_birth': {
            'max_length': 10,
            'pattern': r'^\d{4}-\d{2}-\d{2}$',
            'description': 'YYYY-MM-DD format only',
            'type': str
        },
        'sex': {
            'max_length': 1,
            'pattern': r'^[MFO]$',
            'description': 'M (Male), F (Female), or O (Other) only',
            'type': str
        },
        'issuing_country': {
            'max_length': 100,
            'pattern': r'^[a-zA-Z\s]{2,100}$',
            'description': 'Letters and spaces only (2-100 chars)',
            'type': str
        },
        'id_type': {
            'max_length': 50,
            'pattern': r"^[a-zA-Z\s'\-]{2,50}$",
            'description': "Letters, spaces, hyphens, apostrophes (2-50 chars)",
            'type': str
        }
    }
    
    @classmethod
    def get_rules_for_id_type(cls, id_type: str) -> Dict[str, Dict]:
        """
        Get validation rules for a specific ID type from field mappings.
        Falls back to FALLBACK_RULES if ID type not found.
        
        Args:
            id_type: Type of ID (e.g., 'Ghana Card', 'Passport')
        
        Returns:
            Dictionary of field validation rules
        """
        try:
            fields = get_id_type_fields(id_type)
            rules = {}
            
            for field_name, field in fields.items():
                rules[field_name] = {
                    'max_length': field.max_length,
                    'pattern': field.regex_pattern,
                    'description': f"{field.display_name} (required={field.category.name})",
                    'type': str,
                    'min_length': field.min_length
                }
            
            return rules
        except (KeyError, ValueError):
            # Fallback to generic rules if ID type not found
            return cls.FALLBACK_RULES
    
    @staticmethod
    def sanitize_input(value: str, max_length: int = 500) -> str:
        """
        Sanitize input by removing potentially dangerous characters and limiting length.
        
        Args:
            value: Input string to sanitize
            max_length: Maximum length allowed
        
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return ""
        
        # Strip whitespace
        value = value.strip()
        
        # Limit length to prevent DoS
        value = value[:max_length]
        
        return value
    
    @staticmethod
    def validate_field(field_name: str, value: Any, id_type: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validate a single field against its rules.
        Uses ID type-specific rules from field mappings if provided, otherwise uses fallback rules.
        
        Args:
            field_name: Name of the field to validate
            value: Value to validate
            id_type: Optional ID type to use specific field rules
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Try to use field mapping validation if id_type provided
        if id_type:
            is_valid, error_msg = field_mapping_validate(id_type, field_name, value)
            if not is_valid:
                return False, error_msg
            return True, ""
        
        # Fallback to generic validation
        rules = InputValidator.FALLBACK_RULES
        
        # Check if field is known
        if field_name not in rules:
            return False, f"Unknown field: {field_name}"
        
        rule = rules[field_name]
        
        # Type check
        if not isinstance(value, rule['type']):
            return False, f"{field_name} must be {rule['type'].__name__}, got {type(value).__name__}"
        
        # Empty check
        if not value or (isinstance(value, str) and not value.strip()):
            return False, f"{field_name} cannot be empty"
        
        # Length check
        if len(value) > rule['max_length']:
            return False, f"{field_name} exceeds max length ({rule['max_length']} chars)"
        
        # Pattern check
        if not re.match(rule['pattern'], value.strip()):
            return False, f"{field_name} format invalid: {rule['description']}"
        
        # Special validation for dates
        if field_name == 'date_of_birth':
            is_valid_date, date_error = InputValidator._validate_date(value)
            if not is_valid_date:
                return False, date_error
        
        return True, ""
    
    @staticmethod
    def _validate_date(date_str: str) -> Tuple[bool, str]:
        """Validate date format and reasonable values."""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Check if date is reasonable (not in future, not too old)
            today = datetime.now()
            if date_obj > today:
                return False, "Date of birth cannot be in the future"
            
            age = today.year - date_obj.year
            if age > 150:
                return False, "Date of birth seems invalid (age > 150)"
            
            if age < 13:
                return False, "Person must be at least 13 years old"
            
            return True, ""
        except ValueError:
            return False, "Invalid date format"
    
    @staticmethod
    def validate_form_data(form_data: Dict[str, Any], id_type: Optional[str] = None) -> Tuple[bool, Dict[str, str], Dict[str, Any]]:
        """
        Validate entire form data.
        Uses ID type-specific field validation if id_type provided.
        
        Args:
            form_data: Dictionary of form fields
            id_type: Optional ID type for specific field validation
        
        Returns:
            Tuple of (all_valid, errors_dict, cleaned_data_dict)
        """
        errors = {}
        cleaned_data = {}
        
        # Use field mapping validation if id_type provided
        if id_type:
            is_valid, form_errors = field_mapping_validate_form(id_type, form_data)
            if not is_valid and form_errors:
                errors = form_errors
            
            # Still sanitize and clean data
            for field_name, value in form_data.items():
                if not value:
                    continue
                
                if isinstance(value, str):
                    sanitized = InputValidator.sanitize_input(value)
                else:
                    sanitized = value
                
                if field_name not in errors:
                    cleaned_data[field_name] = sanitized
        else:
            # Generic validation without ID type
            for field_name, value in form_data.items():
                # Skip empty/none values for optional fields
                if not value:
                    continue
                
                # Sanitize
                if isinstance(value, str):
                    sanitized = InputValidator.sanitize_input(value)
                else:
                    sanitized = value
                
                # Validate
                is_valid, error_msg = InputValidator.validate_field(field_name, sanitized)
                
                if not is_valid:
                    errors[field_name] = error_msg
                else:
                    cleaned_data[field_name] = sanitized
        
        all_valid = len(errors) == 0
        return all_valid, errors, cleaned_data
    
    @staticmethod
    def validate_ghana_pin(pin: str) -> Tuple[bool, str]:
        """
        Validate Ghana PIN format: GHA-000000000-0
        
        Args:
            pin: PIN to validate
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not isinstance(pin, str):
            return False, "PIN must be a string"
        
        pin = pin.strip()
        
        if not re.match(r"^GHA-\d{9}-\d$", pin):
            return False, "Ghana PIN format must be GHA-000000000-0"
        
        return True, "Valid Ghana PIN"
    
    @staticmethod
    def validate_voter_id(voter_id: str) -> Tuple[bool, str]:
        """
        Validate Voter ID format (10 digits).
        
        Args:
            voter_id: Voter ID to validate
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not isinstance(voter_id, str):
            return False, "Voter ID must be a string"
        
        voter_id = voter_id.strip()
        
        if not re.match(r"^\d{10}$", voter_id):
            return False, "Voter ID must be exactly 10 digits"
        
        return True, "Valid Voter ID"
    
    @staticmethod
    def validate_driver_license(license_num: str) -> Tuple[bool, str]:
        """
        Validate Driver's License format.
        
        Args:
            license_num: License number to validate
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not isinstance(license_num, str):
            return False, "License number must be a string"
        
        license_num = license_num.strip()
        
        if not re.match(r"^[A-Za-z0-9\-/ ]{5,20}$", license_num):
            return False, "Driver's License format invalid (5-20 alphanumeric chars, hyphens/slashes allowed)"
        
        return True, "Valid Driver's License number"
    
    @staticmethod
    def validate_passport_number(passport_num: str) -> Tuple[bool, str]:
        """
        Validate Passport number format.
        
        Args:
            passport_num: Passport number to validate
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not isinstance(passport_num, str):
            return False, "Passport number must be a string"
        
        passport_num = passport_num.strip()
        
        if not re.match(r"^[A-Za-z0-9]{5,25}$", passport_num):
            return False, "Passport number must be 5-25 alphanumeric characters"
        
        return True, "Valid Passport number"
    
    @staticmethod
    def validate_id_field(id_type: str, id_number: str) -> Tuple[bool, str]:
        """
        Validate ID number based on ID type.
        
        Args:
            id_type: Type of ID card
            id_number: ID number to validate
        
        Returns:
            Tuple of (is_valid, message)
        """
        id_type_lower = id_type.lower() if id_type else ""
        
        if "ghana" in id_type_lower and "card" in id_type_lower:
            return InputValidator.validate_ghana_pin(id_number)
        elif "voter" in id_type_lower:
            return InputValidator.validate_voter_id(id_number)
        elif "driver" in id_type_lower:
            return InputValidator.validate_driver_license(id_number)
        elif "passport" in id_type_lower:
            return InputValidator.validate_passport_number(id_number)
        else:
            return InputValidator.validate_field('id_number', id_number)


if __name__ == "__main__":
    # Test validation
    print("Testing InputValidator...")
    print()
    
    # Test valid Ghana PIN
    is_valid, msg = InputValidator.validate_ghana_pin("GHA-123456789-0")
    print(f"✓ Ghana PIN valid: {is_valid} - {msg}")
    
    # Test invalid Ghana PIN
    is_valid, msg = InputValidator.validate_ghana_pin("INVALID")
    print(f"✗ Invalid Ghana PIN: {is_valid} - {msg}")
    
    # Test form data validation
    form_data = {
        'id_number': 'GHA-123456789-0',
        'surname': 'Doe',
        'firstname': 'John',
        'date_of_birth': '1990-01-01',
        'sex': 'M'
    }
    
    all_valid, errors, cleaned = InputValidator.validate_form_data(form_data)
    print(f"\nForm validation: {all_valid}")
    if errors:
        print(f"Errors: {errors}")
    print(f"Cleaned data: {cleaned}")
