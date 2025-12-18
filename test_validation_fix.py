"""
Test script to validate the ID comparison fix
"""
import sys
from verify import compare_ocr_with_user_input
from id_field_mappings import get_required_match_fields

def test_ghana_card_mismatch():
    """Test case: User entered different ID than extracted from card"""
    print("=" * 80)
    print("TEST: Ghana Card ID Number Mismatch")
    print("=" * 80)
    
    # Simulate user input (what they typed in the form)
    user_data = {
        'ghana_pin': 'GHA-634057782-2',  # User entered this
        'surname': 'NSIA',
        'firstname': 'KWAME',
        'full_name': 'KWAME NSIA',
        'date_of_birth': '28/11/1978',
        'sex': 'M'
    }
    
    # Simulate OCR extraction (what Gemini extracted from the card)
    ocr_data = {
        'ghana_pin': 'GHA-392875782-1',  # Card actually shows this (DIFFERENT!)
        'surname': 'NSIAH',
        'firstname': 'KWAME',
        'full_name': 'KWAME NSIAH',
        'date_of_birth': '28/11/1978',
        'sex': 'M'
    }
    
    id_type = 'Ghana Card'
    
    print(f"\n📋 ID Type: {id_type}")
    print(f"\n👤 User Input:")
    for key, value in user_data.items():
        print(f"  {key}: {value}")
    
    print(f"\n🤖 OCR Extracted:")
    for key, value in ocr_data.items():
        print(f"  {key}: {value}")
    
    print(f"\n🔍 Required Fields for Comparison:")
    required_fields = get_required_match_fields(id_type)
    print(f"  {required_fields}")
    
    print(f"\n⚙️ Running Comparison...")
    comparison = compare_ocr_with_user_input(id_type, user_data, ocr_data)
    
    print(f"\n📊 COMPARISON RESULTS:")
    print(f"  Valid: {comparison['valid']}")
    print(f"  Passed Fields: {comparison['passed_fields']}")
    print(f"  Failed Fields: {comparison['failed_fields']}")
    print(f"  Missing Fields: {comparison['missing_fields']}")
    print(f"  Message: {comparison['message']}")
    
    print(f"\n📝 DETAILED FIELD COMPARISON:")
    for field_name, details in comparison['details'].items():
        status = "✓ MATCH" if details['match'] else "✗ MISMATCH"
        print(f"\n  {status} - {field_name}")
        print(f"    User Value:  '{details['user_value']}'")
        print(f"    OCR Value:   '{details['ocr_value']}'")
        print(f"    Message:     {details['message']}")
        print(f"    Type:        {details['type']}")
    
    print(f"\n{'='*80}")
    
    # Validation
    if comparison['valid']:
        print("❌ TEST FAILED: System marked as VALID when ID numbers don't match!")
        return False
    else:
        if 'ghana_pin' in comparison['failed_fields']:
            print("✅ TEST PASSED: System correctly detected ID number mismatch!")
            return True
        else:
            print("⚠️  TEST PARTIAL: System marked as invalid, but didn't flag ghana_pin")
            return False

def test_ghana_card_match():
    """Test case: User entered same ID as extracted from card"""
    print("\n" + "=" * 80)
    print("TEST: Ghana Card ID Number Match")
    print("=" * 80)
    
    # Both user and OCR have same data
    user_data = {
        'ghana_pin': 'GHA-634057782-2',
        'surname': 'NSIA',
        'firstname': 'KWAME',
        'full_name': 'KWAME NSIA',
        'date_of_birth': '28/11/1978',
        'sex': 'M'
    }
    
    ocr_data = {
        'ghana_pin': 'GHA-634057782-2',  # SAME as user input
        'surname': 'NSIA',
        'firstname': 'KWAME',
        'full_name': 'KWAME NSIA',
        'date_of_birth': '28/11/1978',
        'sex': 'M'
    }
    
    id_type = 'Ghana Card'
    
    print(f"\n📋 ID Type: {id_type}")
    print(f"\n👤 User Input: ghana_pin = {user_data['ghana_pin']}")
    print(f"🤖 OCR Extract: ghana_pin = {ocr_data['ghana_pin']}")
    
    comparison = compare_ocr_with_user_input(id_type, user_data, ocr_data)
    
    print(f"\n📊 Result: {'✓ VALID' if comparison['valid'] else '✗ INVALID'}")
    print(f"  Failed Fields: {comparison['failed_fields']}")
    
    print(f"\n{'='*80}")
    
    if comparison['valid']:
        print("✅ TEST PASSED: System correctly marked matching data as VALID")
        return True
    else:
        print("❌ TEST FAILED: System incorrectly marked matching data as INVALID")
        return False

if __name__ == '__main__':
    print("\n🧪 ID VALIDATION FIX - TEST SUITE")
    print("="*80)
    
    try:
        # Run tests
        test1_result = test_ghana_card_mismatch()
        test2_result = test_ghana_card_match()
        
        print("\n" + "="*80)
        print("📈 TEST SUMMARY")
        print("="*80)
        print(f"Test 1 (Mismatch Detection): {'✅ PASS' if test1_result else '❌ FAIL'}")
        print(f"Test 2 (Match Detection):    {'✅ PASS' if test2_result else '❌ FAIL'}")
        
        if test1_result and test2_result:
            print("\n🎉 ALL TESTS PASSED! The fix is working correctly.")
            sys.exit(0)
        else:
            print("\n❌ SOME TESTS FAILED! There are still issues to fix.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
