Phase 3B - Dynamic Form Generation & UI Integration
===================================================

SCOPE: Update Streamlit app to use Phase 3 field mappings for dynamic form generation

================================================================================
TASK 1: UPDATE app.py FOR DYNAMIC FORMS
================================================================================

CURRENT STATE:
- Hardcoded form fields for each ID type
- Separate validation logic per type
- Form generation not reusable

REQUIRED CHANGES:
1. Import from id_field_mappings:
   - get_user_input_fields()
   - get_id_type_fields()
   - ID_TYPE_REGISTRY

2. Implement dynamic form generation:
   ```python
   def generate_form(id_type):
       fields = get_user_input_fields(id_type)
       form_data = {}
       for field_name, field_obj in fields.items():
           st.text_input(field_obj.display_name, key=field_name)
       return form_data
   ```

3. Replace hardcoded sections with dynamic generation

4. Update form validation to use id_type parameter:
   ```python
   all_valid, errors, cleaned = InputValidator.validate_form_data(
       form_data, id_type=selected_id_type
   )
   ```

EXPECTED OUTCOME:
- Single form template supporting all 5 ID types
- Form fields change based on ID type selection
- Validation rules automatically applied per type

================================================================================
TASK 2: ADD OCR COMPARISON TO VERIFICATION FLOW
================================================================================

CURRENT VERIFICATION FLOW:
1. User enters form data
2. Validate form data
3. Extract OCR from image
4. Compare extracted text to entered data

ENHANCED FLOW WITH PHASE 3:
1. User enters form data → validate with id_type-specific rules
2. Extract OCR from image using Gemini
3. Compare OCR vs user input using intelligent field matching:
   - Exact match for IDs
   - Date format normalization
   - Fuzzy matching for names
   - Enum matching for gender/class
4. Display detailed results to user:
   - Which fields matched
   - Which fields mismatched
   - Confidence scores

IMPLEMENTATION:
```python
from verify import compare_ocr_with_user_input

# After form validation and OCR extraction:
comparison = compare_ocr_with_user_input(id_type, user_data, ocr_data)

if comparison['valid']:
    st.success("Verification successful!")
else:
    st.error("Verification failed")
    st.write("Mismatches:")
    for field in comparison['failed_fields']:
        st.write(f"  • {field}: {comparison['details'][field]['message']}")
```

================================================================================
TASK 3: DISPLAY DETAILED RESULTS
================================================================================

RESULT COMPONENTS TO DISPLAY:

1. Overall Result Badge:
   - "✓ VERIFIED" (green) if valid
   - "✗ FAILED" (red) if not valid

2. Field Match Summary:
   - Passed fields: ✓ field_name (match_type)
   - Failed fields: ✗ field_name (reason)
   - Missing fields: ? field_name (no value)

3. Detailed Comparison:
   - Show user vs OCR values side-by-side
   - Highlight formatting differences
   - Show similarity scores for fuzzy matches

4. Confidence Metrics:
   - Fields passed: X/Y
   - Match confidence: XX%
   - Recommended action: APPROVE / REVIEW / REJECT

================================================================================
TESTING STRATEGY
================================================================================

1. UNIT TESTS FOR FORM GENERATION:
   - Generate forms for each ID type
   - Verify correct fields appear
   - Check field ordering

2. INTEGRATION TESTS:
   - Form generation + validation
   - Form data + OCR extraction + comparison
   - End-to-end workflow

3. UI TESTS (MANUAL):
   - Form displays correctly
   - Fields update on ID type change
   - Results display properly
   - Error messages show clearly

================================================================================
ACCEPTANCE CRITERIA
================================================================================

✓ Single form template supports all 5 ID types
✓ Form fields change when ID type is selected
✓ All fields properly validated with ID-type-specific rules
✓ OCR results intelligently compared to user input
✓ Detailed mismatch information displayed to user
✓ All existing tests still passing
✓ New integration tests for form generation (10+ tests)
✓ UI displays comparison results clearly
✓ Error handling for invalid inputs

================================================================================
EFFORT ESTIMATE
================================================================================

- Form generation refactoring: 2-3 hours
- Integration with OCR comparison: 1-2 hours
- UI result display: 1-2 hours
- Testing: 2-3 hours
- Total: 6-10 hours

================================================================================
DELIVERABLES
================================================================================

1. Updated app.py:
   - Dynamic form generation
   - OCR comparison integration
   - Result display with details

2. Integration tests:
   - Form generation tests
   - End-to-end workflow tests
   - Result display tests

3. Documentation:
   - Updated app.py docstrings
   - Phase 3B completion summary

================================================================================
SUCCESS METRICS
================================================================================

1. Code Quality:
   - All tests passing (including new tests)
   - No regressions from previous phases
   - <5 warnings/issues in code analysis

2. Functionality:
   - Forms work for all 5 ID types
   - OCR comparison produces correct results
   - UI displays results clearly

3. Performance:
   - Form generation: <100ms
   - OCR comparison: <500ms
   - UI rendering: <1s

4. User Experience:
   - Clear feedback on verification status
   - Detailed mismatch information
   - Easy to understand results

================================================================================
NOTES
================================================================================

- Leverages all Phase 3 infrastructure (field mappings, OCR comparison)
- Maintains backward compatibility with existing code
- Extensible for adding new ID types in future
- Can be deployed incrementally (one form at a time)

================================================================================
