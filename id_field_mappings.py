"""
ID Field Mappings - Defines structure and requirements for each ID type.
Maps user input fields, OCR extraction fields, and validation rules.
"""

from typing import Dict, List, Set, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

# ============================================================================
# FIELD CATEGORIES
# ============================================================================

class FieldCategory(Enum):
    """Field importance and handling category."""
    REQUIRED = "required"      # Must be present, exact match with OCR
    OPTIONAL = "optional"      # Present but not critical
    OCR_ONLY = "ocr_only"      # Extracted from OCR only, not user input
    DISPLAY = "display"        # For display purposes only
    SECURITY = "security"      # Sensitive field (CVV, PIN, etc.)


@dataclass
class IDField:
    """Definition of a single ID field."""
    name: str                          # Field identifier (e.g., 'full_name')
    display_name: str                  # User-friendly name
    category: FieldCategory            # How to treat this field
    regex_pattern: Optional[str] = None # Validation regex
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    sensitive: bool = False            # Should not be logged
    
    def validate(self, value: str) -> Tuple[bool, str]:
        """Validate field value. Returns (is_valid, error_message)."""
        if not value and self.category == FieldCategory.REQUIRED:
            return False, f"{self.display_name} is required"
        
        if value and self.min_length and len(value) < self.min_length:
            return False, f"{self.display_name} must be at least {self.min_length} characters"
        
        if value and self.max_length and len(value) > self.max_length:
            return False, f"{self.display_name} must not exceed {self.max_length} characters"
        
        if value and self.regex_pattern:
            import re
            if not re.match(self.regex_pattern, value):
                return False, f"{self.display_name} format is invalid"
        
        return True, ""


# ============================================================================
# GHANA NATIONAL ID (GHANA CARD)
# ============================================================================

# KYC Essential Fields Only
GHANA_CARD_FIELDS = {
    'full_name': IDField(
        name='full_name',
        display_name='Full Name',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^[A-Za-z\s\-\'\.]{3,100}$',
        min_length=3,
        max_length=100
    ),
    'ghana_pin': IDField(
        name='ghana_pin',
        display_name='Ghana Card Number (PIN)',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^GHA-\d{9}-\d$',
    ),
    'date_of_birth': IDField(
        name='date_of_birth',
        display_name='Date of Birth',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
    ),
    'sex': IDField(
        name='sex',
        display_name='Sex',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^[MFO]$|^(Male|Female|Other)$',
    ),
}

GHANA_CARD_USER_INPUT_FIELDS = [
    'full_name', 'ghana_pin', 'date_of_birth', 'sex'
]

GHANA_CARD_OCR_FIELDS = [
    'full_name', 'ghana_pin', 'date_of_birth', 'sex'
]

GHANA_CARD_REQUIRED_MATCH = [
    'ghana_pin', 'full_name', 'date_of_birth', 'sex'
]


# ============================================================================
# GHANA PASSPORT - KYC Essentials
# ============================================================================

PASSPORT_FIELDS = {
    'full_name': IDField(
        name='full_name',
        display_name='Full Name',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^[A-Za-z\s\-\'\.]{3,100}$',
        min_length=3,
        max_length=100
    ),
    'passport_number': IDField(
        name='passport_number',
        display_name='Passport Number',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^[A-Z][0-9]{7}$',  # Ghana format: G1234567
    ),
    'date_of_birth': IDField(
        name='date_of_birth',
        display_name='Date of Birth',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^\d{4}-\d{2}-\d{2}$',
    ),
    'sex': IDField(
        name='sex',
        display_name='Sex',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^[MFO]$|^(Male|Female|Other)$',
    ),
    'expiry_date': IDField(
        name='expiry_date',
        display_name='Expiry Date',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^\d{4}-\d{2}-\d{2}$',
    ),
}

PASSPORT_USER_INPUT_FIELDS = [
    'full_name', 'passport_number', 'date_of_birth', 'sex', 'expiry_date'
]

PASSPORT_OCR_FIELDS = [
    'full_name', 'passport_number', 'date_of_birth', 'sex', 'expiry_date'
]

PASSPORT_REQUIRED_MATCH = [
    'passport_number', 'full_name', 'date_of_birth', 'sex'
]


# ============================================================================
# VOTER ID - KYC Essentials
# ============================================================================

VOTER_ID_FIELDS = {
    'full_name': IDField(
        name='full_name',
        display_name='Full Name',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^[A-Za-z\s\-\'\.]{3,100}$',
    ),
    'voter_id_number': IDField(
        name='voter_id_number',
        display_name='Voter ID Number',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^\d{10}$',  # 10 digits
    ),
    'date_of_birth': IDField(
        name='date_of_birth',
        display_name='Date of Birth',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^\d{4}-\d{2}-\d{2}$',
    ),
    'sex': IDField(
        name='sex',
        display_name='Sex',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^[MFO]$|^(Male|Female|Other)$',
    ),
}

VOTER_ID_USER_INPUT_FIELDS = [
    'full_name', 'voter_id_number', 'date_of_birth', 'sex'
]

VOTER_ID_OCR_FIELDS = [
    'full_name', 'voter_id_number', 'date_of_birth', 'sex'
]

VOTER_ID_REQUIRED_MATCH = [
    'voter_id_number', 'full_name', 'date_of_birth', 'sex'
]


# ============================================================================
# DRIVER'S LICENSE - KYC Essentials
# ============================================================================

DRIVERS_LICENSE_FIELDS = {
    'full_name': IDField(
        name='full_name',
        display_name='Full Name',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^[A-Za-z\s\-\'\.]{3,100}$',
    ),
    'licence_number': IDField(
        name='licence_number',
        display_name='License Number',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^[A-Za-z0-9\-/ ]{5,20}$',
    ),
    'date_of_birth': IDField(
        name='date_of_birth',
        display_name='Date of Birth',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^\d{4}-\d{2}-\d{2}$',
    ),
    'expiry_date': IDField(
        name='expiry_date',
        display_name='Expiry Date',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^\d{4}-\d{2}-\d{2}$',
    ),
}

DRIVERS_LICENSE_USER_INPUT_FIELDS = [
    'full_name', 'licence_number', 'date_of_birth', 'expiry_date'
]

DRIVERS_LICENSE_OCR_FIELDS = [
    'full_name', 'licence_number', 'date_of_birth', 'expiry_date'
]

DRIVERS_LICENSE_REQUIRED_MATCH = [
    'licence_number', 'full_name', 'date_of_birth'
]


# ============================================================================
# BANK CARD - KYC Essentials (Minimal)
# ============================================================================

BANK_CARD_FIELDS = {
    'cardholder_name': IDField(
        name='cardholder_name',
        display_name='Cardholder Name',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^[A-Za-z\s\-\'\.]{3,100}$',
    ),
    'card_number': IDField(
        name='card_number',
        display_name='Card Number (last 4 digits)',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^\d{4}$',  # Last 4 digits only for security
        sensitive=True,
    ),
    'expiry_date': IDField(
        name='expiry_date',
        display_name='Expiry Date',
        category=FieldCategory.REQUIRED,
        regex_pattern=r'^\d{2}/\d{2}$',  # MM/YY format
    ),
}

BANK_CARD_USER_INPUT_FIELDS = [
    'cardholder_name', 'card_number', 'expiry_date'
]

BANK_CARD_OCR_FIELDS = [
    'cardholder_name', 'card_number', 'expiry_date'
]

BANK_CARD_REQUIRED_MATCH = [
    'cardholder_name', 'card_number', 'expiry_date'
]


# ============================================================================
# MASTER REGISTRY
# ============================================================================

ID_TYPE_REGISTRY = {
    'Ghana Card': {
        'fields': GHANA_CARD_FIELDS,
        'user_input_fields': GHANA_CARD_USER_INPUT_FIELDS,
        'ocr_fields': GHANA_CARD_OCR_FIELDS,
        'required_match': GHANA_CARD_REQUIRED_MATCH,
        'description': 'Ghana National Identification Card (Ghana Card)',
    },
    'Ghana Passport': {
        'fields': PASSPORT_FIELDS,
        'user_input_fields': PASSPORT_USER_INPUT_FIELDS,
        'ocr_fields': PASSPORT_OCR_FIELDS,
        'required_match': PASSPORT_REQUIRED_MATCH,
        'description': 'Ghana Passport (ICAO-compliant)',
    },
    'Voter ID': {
        'fields': VOTER_ID_FIELDS,
        'user_input_fields': VOTER_ID_USER_INPUT_FIELDS,
        'ocr_fields': VOTER_ID_OCR_FIELDS,
        'required_match': VOTER_ID_REQUIRED_MATCH,
        'description': 'Ghana Voter\'s Identification Card (New)',
    },
    'Driver\'s License': {
        'fields': DRIVERS_LICENSE_FIELDS,
        'user_input_fields': DRIVERS_LICENSE_USER_INPUT_FIELDS,
        'ocr_fields': DRIVERS_LICENSE_OCR_FIELDS,
        'required_match': DRIVERS_LICENSE_REQUIRED_MATCH,
        'description': 'Ghana Driver\'s License',
    },
    'Bank Card': {
        'fields': BANK_CARD_FIELDS,
        'user_input_fields': BANK_CARD_USER_INPUT_FIELDS,
        'ocr_fields': BANK_CARD_OCR_FIELDS,
        'required_match': BANK_CARD_REQUIRED_MATCH,
        'description': 'Bank Card (Debit/Credit/Prepaid)',
    },
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_id_type_fields(id_type: str) -> Dict[str, IDField]:
    """Get all field definitions for an ID type."""
    if id_type not in ID_TYPE_REGISTRY:
        raise ValueError(f"Unknown ID type: {id_type}")
    return ID_TYPE_REGISTRY[id_type]['fields']


def get_user_input_fields(id_type: str) -> List[str]:
    """Get fields to display in user input form for an ID type."""
    if id_type not in ID_TYPE_REGISTRY:
        raise ValueError(f"Unknown ID type: {id_type}")
    return ID_TYPE_REGISTRY[id_type]['user_input_fields']


def get_ocr_fields(id_type: str) -> List[str]:
    """Get fields to extract from OCR for an ID type."""
    if id_type not in ID_TYPE_REGISTRY:
        raise ValueError(f"Unknown ID type: {id_type}")
    return ID_TYPE_REGISTRY[id_type]['ocr_fields']


def get_required_match_fields(id_type: str) -> List[str]:
    """Get fields that must match between user input and OCR."""
    if id_type not in ID_TYPE_REGISTRY:
        raise ValueError(f"Unknown ID type: {id_type}")
    return ID_TYPE_REGISTRY[id_type]['required_match']


def validate_id_field(id_type: str, field_name: str, value: str) -> Tuple[bool, str]:
    """Validate a single field for an ID type."""
    fields = get_id_type_fields(id_type)
    if field_name not in fields:
        return False, f"Unknown field: {field_name}"
    return fields[field_name].validate(value)


def validate_id_form(id_type: str, form_data: Dict[str, str]) -> Tuple[bool, Dict[str, str]]:
    """Validate all fields in a form. Returns (is_valid, errors_dict)."""
    errors = {}
    fields = get_id_type_fields(id_type)
    user_input_fields = get_user_input_fields(id_type)
    
    for field_name in user_input_fields:
        if field_name in fields:
            field_def = fields[field_name]
            value = form_data.get(field_name, '')
            is_valid, error_msg = field_def.validate(value)
            if not is_valid:
                errors[field_name] = error_msg
    
    return len(errors) == 0, errors


if __name__ == '__main__':
    # Example usage
    print("=== ID Field Mappings Example ===\n")
    
    # Show Ghana Card fields
    print("Ghana Card - User Input Fields:")
    for field_name in get_user_input_fields('Ghana Card'):
        field = get_id_type_fields('Ghana Card')[field_name]
        print(f"  - {field.display_name}: {field.category.value}")
    
    print("\nGhana Card - Required Match Fields:")
    for field_name in get_required_match_fields('Ghana Card'):
        print(f"  - {field_name}")
    
    # Validate a form
    print("\n=== Form Validation Example ===")
    test_data = {
        'surname': 'Kofi',
        'firstname': 'Kwame',
        'date_of_birth': '1985-05-15',
        'gender': 'M',
        'voter_id_number': '1234567890',
    }
    is_valid, errors = validate_id_form('Voter ID', test_data)
    print(f"Valid: {is_valid}")
    if errors:
        print("Errors:")
        for field, error in errors.items():
            print(f"  - {field}: {error}")
