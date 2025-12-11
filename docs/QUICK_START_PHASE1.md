# 🚀 Quick Start Guide - Phase 1 Modules

## Installation & Setup

### 1. Install Test Dependencies
```bash
pip install pytest pytest-cov python-dotenv
```

### 2. Create `.env` File
```env
GEMINI_API_KEY=your_api_key_here
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### 3. Run Tests
```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html

# Specific module
pytest tests/test_validators.py -v -k "ghana"
```

---

## Quick Examples

### Example 1: Validate User Input
```python
from validators import InputValidator
from exceptions import create_error

# Validate a single field
is_valid, msg = InputValidator.validate_ghana_pin("GHA-123456789-0")
print(f"Valid: {is_valid}, Message: {msg}")

# Validate entire form
form = {
    'id_number': 'GHA-123456789-0',
    'surname': 'Doe',
    'firstname': 'John',
    'date_of_birth': '1990-05-15',
    'sex': 'M'
}

is_valid, errors, cleaned = InputValidator.validate_form_data(form)
if is_valid:
    print(f"✓ Form valid. Cleaned data: {cleaned}")
else:
    print(f"✗ Errors: {errors}")
```

### Example 2: Structured Logging
```python
from logger_config import setup_logging, audit_logger

# Setup
logger = setup_logging(log_level="DEBUG")

# Different log levels
logger.debug("Debug information")
logger.info("Application started")
logger.warning("Deprecated feature used")
logger.error("Operation failed", extra={'user_id': 'user_123'})

# Audit trail
audit_logger.log_submission(
    user_id="user_123",
    submission_data={'id_number': 'GHA-123456789-0'},
    result={'overall': True, 'face_match': True}
)
```

### Example 3: Secure API Key Management
```python
from security import SecretsManager, ConfigurationValidator

# Get API key
try:
    api_key = SecretsManager.get_gemini_api_key()
    print(f"✓ API key loaded (length: {len(api_key)})")
except Exception as e:
    print(f"✗ Error: {e}")

# Validate all config
is_valid, errors = ConfigurationValidator.validate_all()
if is_valid:
    config = ConfigurationValidator.get_validated_config()
    print(f"✓ Config valid: {list(config.keys())}")
else:
    print(f"✗ Config errors: {errors}")
```

### Example 4: Retry API Calls
```python
from retry_utils import retry_api_call
from logger_config import get_logger

logger = get_logger(__name__)

@retry_api_call
def call_gemini_api(image_data, api_key):
    # Your API call here
    # Will automatically retry 3 times on failure
    # with exponential backoff (1s, 2s, 4s)
    return None  # Replace with actual call

try:
    result = call_gemini_api(image, api_key)
except Exception as e:
    logger.error(f"API call failed after retries: {e}")
```

### Example 5: Rate Limiting & Cost Tracking
```python
from rate_limiter import RateLimiter, APIUsageTracker, QuotaEnforcer

# Initialize
limiter = RateLimiter(calls_per_minute=10)
tracker = APIUsageTracker()
enforcer = QuotaEnforcer(tracker, default_monthly_limit=10.0)

user_id = "user_123"

# Check rate limit
allowed, wait_time = limiter.is_allowed(user_id)
if not allowed:
    print(f"Rate limited. Wait {wait_time:.1f}s")
    exit(1)

# Check quota
allowed, info = enforcer.check_quota_before_call(user_id)
if not allowed:
    print(f"Quota exceeded: ${info['current_cost']:.2f}/${info['max_cost']:.2f}")
    exit(1)

# Record API call (simulate 1000 input, 500 output tokens)
cost = tracker.record_api_call(user_id, "gemini-1.5-flash", 1000, 500)
print(f"Call cost: ${cost:.4f}")

# Check stats
stats = tracker.get_user_stats(user_id)
print(f"User stats: {stats}")
```

### Example 6: Error Handling
```python
from exceptions import create_error, ValidationError
from logger_config import get_logger

logger = get_logger(__name__)

try:
    # Some operation
    api_key = ""
    if not api_key:
        raise create_error(
            'API_KEY_INVALID',
            details={'reason': 'Empty API key'},
            exception_class=ValidationError
        )
except ValidationError as e:
    logger.error(f"Validation error: {e.code}")
    
    # Serialize for API response
    error_dict = e.to_dict()
    print(f"Error dict: {error_dict}")
    
    # Display to user
    print(f"User message: {e.user_message}")
```

---

## Testing Examples

### Run Single Test Class
```bash
pytest tests/test_validators.py::TestGhanaPINValidation -v
```

### Run Single Test
```bash
pytest tests/test_validators.py::TestGhanaPINValidation::test_valid_ghana_pin -v
```

### Run Tests Matching Pattern
```bash
pytest tests/ -k "ghana" -v
```

### Run with Coverage Report
```bash
pytest tests/ --cov=validators --cov=rate_limiter --cov-report=term-missing
```

---

## File Quick Reference

| File | Purpose | Key Classes |
|------|---------|-------------|
| `logger_config.py` | Logging setup | `setup_logging()`, `AuditLogger` |
| `validators.py` | Input validation | `InputValidator` |
| `exceptions.py` | Error handling | Exception classes + `ERROR_CATALOG` |
| `retry_utils.py` | Retry logic | `@retry_with_backoff` decorator |
| `security.py` | Secret management | `SecretsManager`, `ConfigurationValidator` |
| `rate_limiter.py` | Rate limiting | `RateLimiter`, `APIUsageTracker` |

---

## Debugging Tips

### Check Logs
```bash
# View latest logs
tail -f logs/id_verification.log

# View errors only
tail -f logs/id_verification_errors.log

# View audit trail (JSON format)
cat logs/audit.log | python -m json.tool | less
```

### Test Validation Rules
```python
from validators import InputValidator

# Test all Ghana PIN formats
test_pins = [
    ("GHA-123456789-0", True),   # Valid
    ("GHA-12345678-0", False),   # Too short
    ("gha-123456789-0", False),  # Lowercase
]

for pin, expected in test_pins:
    is_valid, msg = InputValidator.validate_ghana_pin(pin)
    status = "✓" if is_valid == expected else "✗"
    print(f"{status} {pin}: {is_valid}")
```

### Debug Rate Limiting
```python
from rate_limiter import RateLimiter

limiter = RateLimiter(calls_per_minute=3)

for i in range(5):
    allowed, wait = limiter.is_allowed("test_user")
    remaining = limiter.get_remaining_calls("test_user")
    print(f"Call {i+1}: allowed={allowed}, remaining={remaining}")
```

---

## Common Issues & Solutions

### Issue: Tests import fails
**Solution**: Ensure you're in the project root directory and have installed dependencies:
```bash
cd /path/to/ID_-verification
pip install -r requirements.txt
pip install pytest python-dotenv
```

### Issue: API key not found
**Solution**: Create `.env` file with GEMINI_API_KEY:
```bash
echo 'GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' > .env
```

### Issue: Logs directory permission error
**Solution**: Ensure write permissions:
```bash
mkdir -p logs
chmod 755 logs
```

### Issue: Validation failing unexpectedly
**Solution**: Check whitespace and case:
```python
# These are different
InputValidator.validate_field('name', 'John')      # OK
InputValidator.validate_field('name', 'JOHN')      # OK
InputValidator.validate_field('name', '  john  ')  # Sanitized first
```

---

## Next: Phase 2 Integration

To use these modules in your application:

1. **Update `app.py`**:
   - Add `from logger_config import setup_logging`
   - Add `from validators import InputValidator`
   - Validate form inputs before processing

2. **Update `gemini_card_detector.py`**:
   - Add `@retry_api_call` decorator
   - Add proper error handling

3. **Update `verify.py`**:
   - Use validation for all inputs
   - Use rate limiting before API calls

See `PHASE_1_COMPLETE.md` for detailed integration guide.

---

**Phase 1 Status**: ✅ Complete  
**Test Coverage**: 340+ tests  
**Ready for integration**: Yes
