"""
Unit tests for retry logic.
"""

import pytest
import time
from retry_utils import (
    retry_with_backoff,
    retry_api_call,
    retry_network_call,
    retry_file_operation,
    RetryConfig
)


class TestRetryDecorator:
    """Test basic retry decorator functionality."""
    
    def test_retry_on_first_try_success(self):
        """Test function that succeeds on first try."""
        @retry_with_backoff(max_retries=3)
        def successful_func():
            return "success"
        
        result = successful_func()
        assert result == "success"
    
    def test_retry_on_eventual_success(self):
        """Test function that eventually succeeds."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, initial_delay=0.01, backoff_factor=1.5)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Simulated error")
            return "success"
        
        result = flaky_func()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_exhaustion(self):
        """Test that function fails after max retries."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")
        
        with pytest.raises(ConnectionError):
            always_fails()
        
        assert call_count == 2
    
    def test_retry_with_custom_delay(self):
        """Test retry with custom initial delay."""
        start_time = time.time()
        
        @retry_with_backoff(max_retries=2, initial_delay=0.1, backoff_factor=1.0)
        def slow_fail():
            raise ConnectionError("Fail")
        
        with pytest.raises(ConnectionError):
            slow_fail()
        
        elapsed = time.time() - start_time
        # Should have 1 retry with 0.1s delay
        assert elapsed >= 0.1
    
    def test_retry_exponential_backoff(self):
        """Test exponential backoff timing."""
        call_times = []
        
        @retry_with_backoff(
            max_retries=4,
            initial_delay=0.01,
            backoff_factor=2.0,
            max_delay=0.5
        )
        def track_calls():
            call_times.append(time.time())
            if len(call_times) < 4:
                raise ConnectionError("Fail")
            return "success"
        
        result = track_calls()
        assert result == "success"
        
        # Check delays increase exponentially
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            # Second delay should be roughly double first
            assert delay2 > delay1
    
    def test_retry_max_delay_enforced(self):
        """Test that max delay is enforced."""
        @retry_with_backoff(
            max_retries=5,
            initial_delay=0.1,
            backoff_factor=10.0,
            max_delay=0.2
        )
        def fail_func():
            raise ConnectionError("Fail")
        
        start_time = time.time()
        with pytest.raises(ConnectionError):
            fail_func()
        
        elapsed = time.time() - start_time
        # Max delay should cap the wait times
        assert elapsed < 2.0  # Should be much less than unlimited backoff
    
    def test_retry_specific_exceptions(self):
        """Test retry only on specific exceptions."""
        call_count = 0
        
        @retry_with_backoff(
            max_retries=3,
            exceptions=(ValueError,),
            initial_delay=0.01
        )
        def func_with_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("This should not be retried")
        
        with pytest.raises(TypeError):
            func_with_type_error()
        
        # Should fail immediately without retries
        assert call_count == 1
    
    def test_retry_with_args_and_kwargs(self):
        """Test retry decorator preserves function args and kwargs."""
        @retry_with_backoff(max_retries=1, initial_delay=0.01)
        def add(a, b, c=0):
            return a + b + c
        
        result = add(1, 2, c=3)
        assert result == 6


class TestRetryDecorators:
    """Test predefined retry decorators."""
    
    def test_retry_api_call_decorator(self):
        """Test retry_api_call decorator."""
        call_count = 0
        
        @retry_api_call
        def api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("API timeout")
            return "success"
        
        result = api_call()
        assert result == "success"
        assert call_count == 2
    
    def test_retry_network_call_decorator(self):
        """Test retry_network_call decorator."""
        call_count = 0
        
        @retry_network_call
        def network_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network error")
            return "success"
        
        result = network_call()
        assert result == "success"
    
    def test_retry_file_operation_decorator(self):
        """Test retry_file_operation decorator."""
        call_count = 0
        
        @retry_file_operation
        def file_op():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise IOError("File error")
            return "success"
        
        result = file_op()
        assert result == "success"


class TestRetryExceptionHandling:
    """Test exception handling in retry logic."""
    
    def test_retry_preserves_exception_message(self):
        """Test that exception message is preserved."""
        error_msg = "Specific error message"
        
        @retry_with_backoff(max_retries=1, initial_delay=0.01)
        def fail_func():
            raise ValueError(error_msg)
        
        with pytest.raises(ValueError) as exc_info:
            fail_func()
        
        assert str(exc_info.value) == error_msg
    
    def test_retry_different_exception_types(self):
        """Test retry with multiple exception types."""
        @retry_with_backoff(
            max_retries=3,
            exceptions=(ValueError, TypeError, KeyError),
            initial_delay=0.01
        )
        def multi_error():
            raise ValueError("Value error")
        
        with pytest.raises(ValueError):
            multi_error()


class TestRetryEdgeCases:
    """Test edge cases for retry logic."""
    
    def test_retry_zero_retries(self):
        """Test with zero retries allowed."""
        call_count = 0
        
        @retry_with_backoff(max_retries=0, initial_delay=0.01)
        def fail_once():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Error")
        
        with pytest.raises(ConnectionError):
            fail_once()
        
        # With 0 retries, should still try once
        assert call_count >= 1
    
    def test_retry_one_retry(self):
        """Test with single retry."""
        call_count = 0
        
        @retry_with_backoff(max_retries=1, initial_delay=0.01)
        def fail_once():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Error")
            return "success"
        
        result = fail_once()
        assert result == "success"
        assert call_count == 2
    
    def test_retry_with_very_small_delay(self):
        """Test retry with very small initial delay."""
        @retry_with_backoff(max_retries=2, initial_delay=0.001, backoff_factor=1.5)
        def quick_fail():
            raise ConnectionError("Error")
        
        start = time.time()
        with pytest.raises(ConnectionError):
            quick_fail()
        
        elapsed = time.time() - start
        # Should complete quickly
        assert elapsed < 0.2
    
    def test_retry_function_returns_none(self):
        """Test retry with function returning None."""
        @retry_with_backoff(max_retries=1, initial_delay=0.01)
        def return_none():
            return None
        
        result = return_none()
        assert result is None
    
    def test_retry_function_returns_false(self):
        """Test retry with function returning False."""
        @retry_with_backoff(max_retries=1, initial_delay=0.01)
        def return_false():
            return False
        
        result = return_false()
        assert result is False
    
    def test_retry_with_generator_function(self):
        """Test retry with generator function."""
        @retry_with_backoff(max_retries=1, initial_delay=0.01)
        def gen_func():
            yield 1
            yield 2
        
        result = gen_func()
        # Should return generator object
        assert hasattr(result, '__iter__')


class TestRetryIntegration:
    """Integration tests for retry logic."""
    
    def test_retry_chain_multiple_failures(self):
        """Test retrying through multiple sequential failures."""
        attempt_log = []
        
        @retry_with_backoff(
            max_retries=5,
            initial_delay=0.01,
            backoff_factor=1.5,
            exceptions=(ValueError,)
        )
        def sequential_fails():
            attempt_log.append(len(attempt_log) + 1)
            if len(attempt_log) < 4:
                raise ValueError(f"Attempt {len(attempt_log)} failed")
            return f"Success after {len(attempt_log)} attempts"
        
        result = sequential_fails()
        assert "Success" in result
        assert len(attempt_log) == 4
    
    def test_retry_with_state_mutation(self):
        """Test retry with stateful operations."""
        state = {'counter': 0}
        
        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def increment_counter():
            state['counter'] += 1
            if state['counter'] < 2:
                raise RuntimeError("Not ready")
            return state['counter']
        
        result = increment_counter()
        assert result == 2
        assert state['counter'] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
