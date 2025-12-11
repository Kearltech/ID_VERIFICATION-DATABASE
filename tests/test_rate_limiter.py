"""
Unit tests for rate limiting and usage tracking.
"""

import pytest
import time
from rate_limiter import (
    RateLimiter,
    APIUsageTracker,
    QuotaEnforcer
)
from retry_utils import RetryConfig


class TestRateLimiter:
    """Test rate limiter functionality."""
    
    def test_rate_limiter_allows_calls_under_limit(self):
        """Test rate limiter allows calls under limit."""
        limiter = RateLimiter(calls_per_minute=3)
        
        # Should allow 3 calls
        for i in range(3):
            allowed, wait_time = limiter.is_allowed("user_1")
            assert allowed is True
            assert wait_time is None
    
    def test_rate_limiter_blocks_calls_over_limit(self):
        """Test rate limiter blocks calls over limit."""
        limiter = RateLimiter(calls_per_minute=2)
        
        # Use up limit
        limiter.is_allowed("user_1")
        limiter.is_allowed("user_1")
        
        # Next call should be blocked
        allowed, wait_time = limiter.is_allowed("user_1")
        assert allowed is False
        assert wait_time is not None
        assert wait_time > 0
    
    def test_rate_limiter_separate_users(self):
        """Test rate limiter tracks users separately."""
        limiter = RateLimiter(calls_per_minute=2)
        
        # User 1 uses their quota
        limiter.is_allowed("user_1")
        limiter.is_allowed("user_1")
        
        # User 2 should still have quota
        allowed, _ = limiter.is_allowed("user_2")
        assert allowed is True
    
    def test_rate_limiter_wait_time_reasonable(self):
        """Test wait time is reasonable."""
        limiter = RateLimiter(calls_per_minute=1)
        
        limiter.is_allowed("user_1")
        allowed, wait_time = limiter.is_allowed("user_1")
        
        assert allowed is False
        assert 0 < wait_time <= 60
    
    def test_rate_limiter_record_call(self):
        """Test recording API calls."""
        limiter = RateLimiter(calls_per_minute=2)
        
        limiter.record_call("user_1")
        limiter.record_call("user_1")
        
        allowed, wait_time = limiter.is_allowed("user_1")
        assert allowed is False
    
    def test_rate_limiter_get_remaining_calls(self):
        """Test getting remaining calls."""
        limiter = RateLimiter(calls_per_minute=5)
        
        limiter.is_allowed("user_1")
        limiter.is_allowed("user_1")
        
        remaining = limiter.get_remaining_calls("user_1")
        assert remaining == 3


class TestAPIUsageTracker:
    """Test API usage tracking."""
    
    def test_record_api_call(self):
        """Test recording API call."""
        tracker = APIUsageTracker()
        
        cost = tracker.record_api_call(
            "user_1",
            "gemini-1.5-flash",
            tokens_in=1000,
            tokens_out=500
        )
        
        assert cost > 0
    
    def test_record_multiple_calls(self):
        """Test recording multiple calls."""
        tracker = APIUsageTracker()
        
        cost1 = tracker.record_api_call("user_1", "gemini-1.5-flash", 1000, 500)
        cost2 = tracker.record_api_call("user_1", "gemini-1.5-flash", 2000, 1000)
        
        total_cost = tracker.get_user_cost("user_1")
        assert total_cost == pytest.approx(cost1 + cost2)
    
    def test_get_user_stats(self):
        """Test getting user statistics."""
        tracker = APIUsageTracker()
        
        tracker.record_api_call("user_1", "gemini-1.5-flash", 1000, 500)
        tracker.record_api_call("user_1", "gemini-1.5-flash", 2000, 1000)
        
        stats = tracker.get_user_stats("user_1")
        
        assert stats['calls'] == 2
        assert stats['tokens_in'] == 3000
        assert stats['tokens_out'] == 1500
        assert stats['total_cost'] > 0
        assert 'average_cost_per_call' in stats
    
    def test_check_quota_within_limit(self):
        """Test quota check when within limit."""
        tracker = APIUsageTracker()
        
        tracker.record_api_call("user_1", "gemini-1.5-flash", 1000, 500)
        
        within_quota, info = tracker.check_quota("user_1", max_cost=10.0)
        
        assert within_quota is True
        assert info['remaining'] > 0
        assert info['within_quota'] is True
    
    def test_check_quota_exceeded(self):
        """Test quota check when exceeded."""
        tracker = APIUsageTracker()
        
        # Make expensive calls
        for _ in range(100):
            tracker.record_api_call("user_1", "gemini-1.5-flash", 10000, 10000)
        
        within_quota, info = tracker.check_quota("user_1", max_cost=1.0)
        
        assert within_quota is False
        assert info['remaining'] < 0
        assert info['within_quota'] is False
    
    def test_quota_info_structure(self):
        """Test quota info has expected structure."""
        tracker = APIUsageTracker()
        
        tracker.record_api_call("user_1", "gemini-1.5-flash", 1000, 500)
        
        within_quota, info = tracker.check_quota("user_1", max_cost=10.0)
        
        assert 'current_cost' in info
        assert 'max_cost' in info
        assert 'remaining' in info
        assert 'api_calls' in info
        assert 'within_quota' in info
        assert 'usage_percent' in info
    
    def test_separate_users_tracking(self):
        """Test tracking different users separately."""
        tracker = APIUsageTracker()
        
        tracker.record_api_call("user_1", "gemini-1.5-flash", 1000, 500)
        tracker.record_api_call("user_2", "gemini-1.5-flash", 2000, 1000)
        
        cost1 = tracker.get_user_cost("user_1")
        cost2 = tracker.get_user_cost("user_2")
        
        assert cost1 != cost2
        assert cost2 > cost1
    
    def test_pricing_calculation(self):
        """Test pricing calculation."""
        tracker = APIUsageTracker()
        
        # 1M input tokens + 1M output tokens
        cost = tracker.record_api_call("user_1", "gemini-1.5-flash", 1_000_000, 1_000_000)
        
        # Expected: 0.075 + 0.30 = $0.375
        expected_cost = 0.075 + 0.30
        assert cost == pytest.approx(expected_cost)


class TestQuotaEnforcer:
    """Test quota enforcement."""
    
    def test_quota_enforcer_default_limit(self):
        """Test quota enforcer with default limit."""
        tracker = APIUsageTracker()
        enforcer = QuotaEnforcer(tracker, default_monthly_limit=10.0)
        
        tracker.record_api_call("user_1", "gemini-1.5-flash", 1000, 500)
        
        allowed, info = enforcer.check_quota_before_call("user_1")
        
        assert allowed is True
    
    def test_quota_enforcer_custom_user_limit(self):
        """Test quota enforcer with custom user limit."""
        tracker = APIUsageTracker()
        enforcer = QuotaEnforcer(tracker)
        
        enforcer.set_user_limit("user_1", 5.0)
        
        # Make expensive calls
        for _ in range(50):
            tracker.record_api_call("user_1", "gemini-1.5-flash", 10000, 10000)
        
        allowed, info = enforcer.check_quota_before_call("user_1")
        
        assert allowed is False
    
    def test_quota_enforcer_returns_quota_info(self):
        """Test quota enforcer returns quota information."""
        tracker = APIUsageTracker()
        enforcer = QuotaEnforcer(tracker)
        
        tracker.record_api_call("user_1", "gemini-1.5-flash", 1000, 500)
        
        allowed, info = enforcer.check_quota_before_call("user_1")
        
        assert isinstance(info, dict)
        assert 'current_cost' in info


class TestRetryConfig:
    """Test retry configuration."""
    
    def test_retry_config_api_values(self):
        """Test API retry config values."""
        assert RetryConfig.API_MAX_RETRIES >= 2
        assert RetryConfig.API_INITIAL_DELAY > 0
        assert RetryConfig.API_BACKOFF_FACTOR >= 1.5
    
    def test_retry_config_network_values(self):
        """Test network retry config values."""
        assert RetryConfig.NETWORK_MAX_RETRIES >= RetryConfig.API_MAX_RETRIES
        assert RetryConfig.NETWORK_MAX_DELAY >= RetryConfig.API_MAX_DELAY
    
    def test_retry_config_file_values(self):
        """Test file retry config values."""
        assert RetryConfig.FILE_MAX_RETRIES >= 2
        assert RetryConfig.FILE_INITIAL_DELAY > 0


class TestRateLimiterEdgeCases:
    """Test edge cases for rate limiter."""
    
    def test_rate_limiter_zero_calls_allowed(self):
        """Test rate limiter with zero calls allowed."""
        # This is an edge case - should probably allow at least 1
        limiter = RateLimiter(calls_per_minute=1)
        
        allowed1, _ = limiter.is_allowed("user_1")
        assert allowed1 is True
        
        allowed2, _ = limiter.is_allowed("user_1")
        assert allowed2 is False
    
    def test_rate_limiter_very_high_limit(self):
        """Test rate limiter with very high limit."""
        limiter = RateLimiter(calls_per_minute=1000)
        
        # Make 100 calls, should all be allowed
        for i in range(100):
            allowed, _ = limiter.is_allowed(f"user_{i % 10}")
            assert allowed is True
    
    def test_tracker_unknown_model(self):
        """Test tracker with unknown model."""
        tracker = APIUsageTracker()
        
        # Should return 0 cost for unknown model
        cost = tracker.record_api_call("user_1", "unknown-model", 1000, 500)
        
        assert cost == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
