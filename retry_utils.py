"""
Retry logic with exponential backoff for API calls and resilient operations.
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Type, Tuple
from exceptions import APIError, create_error

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each retry
        max_delay: Maximum delay between retries
        exceptions: Tuple of exceptions to catch and retry on
    
    Returns:
        Decorated function
    
    Example:
        @retry_with_backoff(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
        def call_api():
            # API call that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            delay = initial_delay
            
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        logger.info(
                            f"Retrying {func.__name__} (attempt {attempt}/{max_retries}) "
                            f"after {delay}s delay"
                        )
                        time.sleep(delay)
                    
                    result = func(*args, **kwargs)
                    
                    if attempt > 0:
                        logger.info(f"{func.__name__} succeeded after {attempt} retry attempt(s)")
                    
                    return result
                
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        # Calculate next delay with backoff
                        delay = min(delay * backoff_factor, max_delay)
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {delay}s..."
                        )
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts: {e}"
                        )
                
                except Exception as e:
                    # Don't retry on unexpected exceptions
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                    raise
            
            # All retries exhausted
            if last_exception:
                raise last_exception
            else:
                raise Exception(f"{func.__name__} failed after {max_retries} attempts")
        
        return wrapper
    
    return decorator


class RetryConfig:
    """Configuration for retry behavior."""
    
    # API call defaults
    API_MAX_RETRIES = 3
    API_INITIAL_DELAY = 1.0
    API_BACKOFF_FACTOR = 2.0
    API_MAX_DELAY = 30.0
    
    # Network defaults
    NETWORK_MAX_RETRIES = 5
    NETWORK_INITIAL_DELAY = 0.5
    NETWORK_BACKOFF_FACTOR = 2.0
    NETWORK_MAX_DELAY = 60.0
    
    # File operation defaults
    FILE_MAX_RETRIES = 3
    FILE_INITIAL_DELAY = 0.1
    FILE_BACKOFF_FACTOR = 2.0
    FILE_MAX_DELAY = 10.0


def retry_api_call(func: Callable) -> Callable:
    """Decorator for API calls with standard retry configuration."""
    return retry_with_backoff(
        max_retries=RetryConfig.API_MAX_RETRIES,
        initial_delay=RetryConfig.API_INITIAL_DELAY,
        backoff_factor=RetryConfig.API_BACKOFF_FACTOR,
        max_delay=RetryConfig.API_MAX_DELAY,
        exceptions=(TimeoutError, APIError, ConnectionError)
    )(func)


def retry_network_call(func: Callable) -> Callable:
    """Decorator for network calls with standard retry configuration."""
    return retry_with_backoff(
        max_retries=RetryConfig.NETWORK_MAX_RETRIES,
        initial_delay=RetryConfig.NETWORK_INITIAL_DELAY,
        backoff_factor=RetryConfig.NETWORK_BACKOFF_FACTOR,
        max_delay=RetryConfig.NETWORK_MAX_DELAY,
        exceptions=(TimeoutError, ConnectionError, IOError)
    )(func)


def retry_file_operation(func: Callable) -> Callable:
    """Decorator for file operations with standard retry configuration."""
    return retry_with_backoff(
        max_retries=RetryConfig.FILE_MAX_RETRIES,
        initial_delay=RetryConfig.FILE_INITIAL_DELAY,
        backoff_factor=RetryConfig.FILE_BACKOFF_FACTOR,
        max_delay=RetryConfig.FILE_MAX_DELAY,
        exceptions=(IOError, OSError, FileNotFoundError)
    )(func)


if __name__ == "__main__":
    # Test retry decorator
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    
    print("Testing retry logic...\n")
    
    attempt_count = 0
    
    @retry_with_backoff(max_retries=3, initial_delay=0.5, backoff_factor=2.0)
    def flaky_function():
        global attempt_count
        attempt_count += 1
        print(f"Attempt {attempt_count}")
        
        if attempt_count < 3:
            raise ConnectionError("Simulated network error")
        
        return "Success!"
    
    result = flaky_function()
    print(f"Result: {result}")
    print(f"Total attempts: {attempt_count}")
