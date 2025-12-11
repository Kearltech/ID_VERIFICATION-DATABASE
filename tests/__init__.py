"""
Unit tests for ID Verification system.

This package contains comprehensive tests for all core modules:
- test_validators.py: Input validation and sanitization
- test_exceptions.py: Custom exception handling
- test_rate_limiter.py: Rate limiting and usage tracking
- test_retry_utils.py: Retry logic with exponential backoff

To run all tests:
    pytest tests/ -v
    
To run specific test file:
    pytest tests/test_validators.py -v
    
To run with coverage:
    pytest tests/ --cov=.. --cov-report=html
"""
