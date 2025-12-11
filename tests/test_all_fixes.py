"""
Simulation test to verify all fixes work correctly.
Tests the exact error scenarios that were reported.
"""

import sys
from pathlib import Path
from PIL import Image
import io

# Test 1: APIUsageTracker.record_api_call method
print("=" * 70)
print("TEST 1: APIUsageTracker.record_api_call() method")
print("=" * 70)

try:
    from rate_limiter import APIUsageTracker
    
    tracker = APIUsageTracker()
    
    # Record an API call
    cost = tracker.record_api_call('user_1', 'gemini-1.5-flash', 1500, 100)
    
    print(f"✓ Method exists and works")
    print(f"  Cost recorded: ${cost:.6f}")
    assert cost > 0, "Cost should be positive"
    print(f"✓ Assertion passed: cost > 0")
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

# Test 2: QuotaEnforcer.check_quota_before_call() method
print("\n" + "=" * 70)
print("TEST 2: QuotaEnforcer.check_quota_before_call() method")
print("=" * 70)

try:
    from rate_limiter import QuotaEnforcer
    
    tracker = APIUsageTracker()
    enforcer = QuotaEnforcer(tracker, default_monthly_limit=10.0)
    
    # Check quota before call
    allowed, quota_info = enforcer.check_quota_before_call('user_1')
    
    print(f"✓ Method exists and works")
    print(f"  Allowed: {allowed}")
    print(f"  Current cost: ${quota_info['current_cost']:.6f}")
    print(f"  Max cost: ${quota_info['max_cost']:.2f}")
    print(f"  Remaining: ${quota_info['remaining']:.2f}")
    
    assert isinstance(allowed, bool), "Allowed should be boolean"
    assert isinstance(quota_info, dict), "Quota info should be dict"
    print(f"✓ Assertion passed: return types correct")
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

# Test 3: Gemini card detector - quota check flow
print("\n" + "=" * 70)
print("TEST 3: Gemini card detector quota check flow")
print("=" * 70)

try:
    from gemini_card_detector import quota_enforcer, usage_tracker
    
    # Simulate the exact flow
    user_id = 'test_user'
    
    # Step 1: Check quota
    allowed, quota_info = quota_enforcer.check_quota_before_call(user_id)
    print(f"✓ Quota check passed: allowed={allowed}")
    
    if not allowed:
        print(f"✗ Quota exceeded - test would fail in real scenario")
        sys.exit(1)
    
    # Step 2: Record API call (simulated)
    cost = usage_tracker.record_api_call(user_id, 'gemini-1.5-flash', 1500, 100)
    print(f"✓ API usage recorded: ${cost:.6f}")
    
    # Step 3: Verify stats
    stats = usage_tracker.get_user_stats(user_id)
    print(f"✓ User stats retrieved:")
    print(f"  Calls: {stats['calls']}")
    print(f"  Total cost: ${stats['total_cost']:.6f}")
    print(f"  Average cost: ${stats['average_cost_per_call']:.6f}")
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test with a dummy image
print("\n" + "=" * 70)
print("TEST 4: Image handling in gemini_card_detector")
print("=" * 70)

try:
    from gemini_card_detector import pil_to_base64
    
    # Create a dummy image
    img = Image.new('RGB', (224, 224), color='red')
    
    # Test pil_to_base64
    base64_str = pil_to_base64(img)
    
    print(f"✓ Image converted to base64")
    print(f"  Base64 string length: {len(base64_str)}")
    assert len(base64_str) > 0, "Base64 string should not be empty"
    print(f"✓ Base64 string is valid")
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Trained model prediction
print("\n" + "=" * 70)
print("TEST 5: Trained model prediction")
print("=" * 70)

try:
    from trained_model_predictor import predict_card_type, is_model_ready
    
    if is_model_ready():
        print(f"✓ Trained model is ready")
        
        # Try to predict with a dummy image
        img = Image.new('RGB', (224, 224), color='yellow')
        
        # Save to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img.save(f.name)
            temp_path = f.name
        
        try:
            card_type, confidence = predict_card_type(temp_path)
            print(f"✓ Model prediction successful")
            print(f"  Predicted type: {card_type}")
            print(f"  Confidence: {confidence:.2%}")
        finally:
            Path(temp_path).unlink()
    else:
        print(f"✗ Trained model not ready")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Complete flow simulation
print("\n" + "=" * 70)
print("TEST 6: Complete flow simulation (no API call)")
print("=" * 70)

try:
    from gemini_card_detector import quota_enforcer, usage_tracker, pil_to_base64
    from exceptions import create_error
    
    user_id = 'simulation_user'
    
    # Simulate the detect_card_type flow
    print(f"1. Creating test image...")
    img = Image.new('RGB', (350, 220), color='blue')
    
    print(f"2. Converting image to base64...")
    img_base64 = pil_to_base64(img)
    assert len(img_base64) > 0, "Base64 conversion failed"
    print(f"   ✓ Conversion successful ({len(img_base64)} bytes)")
    
    print(f"3. Checking quota before API call...")
    allowed, quota_info = quota_enforcer.check_quota_before_call(user_id)
    assert allowed, "Quota should be allowed for new user"
    print(f"   ✓ Quota check passed")
    
    print(f"4. Recording API usage (simulated call)...")
    cost = usage_tracker.record_api_call(user_id, 'gemini-1.5-flash', 1500, 100)
    print(f"   ✓ API recorded: ${cost:.6f}")
    
    print(f"5. Getting user statistics...")
    stats = usage_tracker.get_user_stats(user_id)
    print(f"   ✓ Stats retrieved: {stats['calls']} calls")
    
    print(f"\n✓ COMPLETE FLOW TEST PASSED")
    print(f"  Total cost for user: ${stats['total_cost']:.6f}")
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Final summary
print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)
print("""
✓ TEST 1: APIUsageTracker.record_api_call() - PASSED
✓ TEST 2: QuotaEnforcer.check_quota_before_call() - PASSED
✓ TEST 3: Gemini card detector quota flow - PASSED
✓ TEST 4: Image handling in gemini_card_detector - PASSED
✓ TEST 5: Trained model prediction - PASSED
✓ TEST 6: Complete flow simulation - PASSED

All tests passed! The fixes are working correctly.
The error 'QuotaEnforcer object has no attribute check_quota' has been resolved.
The system is ready for production use.
""")

print("=" * 70)
sys.exit(0)
