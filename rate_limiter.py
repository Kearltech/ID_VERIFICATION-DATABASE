"""
Rate limiting and API usage tracking.
Prevents abuse and tracks costs.
"""

import time
import logging
from collections import defaultdict
from threading import Lock
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from exceptions import RateLimitError, create_error

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter for API calls."""
    
    def __init__(self, calls_per_minute: int = 10):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_minute: Maximum API calls allowed per minute
        """
        self.calls_per_minute = calls_per_minute
        self.call_times = defaultdict(list)
        self.lock = Lock()
    
    def is_allowed(self, user_id: str) -> Tuple[bool, Optional[float]]:
        """
        Check if user is allowed to make an API call.
        
        Args:
            user_id: User identifier
        
        Returns:
            Tuple of (is_allowed, wait_time_in_seconds)
        """
        with self.lock:
            now = time.time()
            minute_ago = now - 60
            
            # Remove calls older than 1 minute
            self.call_times[user_id] = [
                t for t in self.call_times[user_id] if t > minute_ago
            ]
            
            # Check if under limit
            if len(self.call_times[user_id]) < self.calls_per_minute:
                self.call_times[user_id].append(now)
                return True, None
            
            # Calculate wait time
            oldest_call = self.call_times[user_id][0]
            wait_time = 60 - (now - oldest_call)
            
            return False, max(0, wait_time)
    
    def record_call(self, user_id: str):
        """Record an API call for a user."""
        with self.lock:
            self.call_times[user_id].append(time.time())
    
    def get_remaining_calls(self, user_id: str) -> int:
        """Get remaining API calls for user in current minute."""
        with self.lock:
            now = time.time()
            minute_ago = now - 60
            
            recent_calls = [
                t for t in self.call_times[user_id] if t > minute_ago
            ]
            
            return max(0, self.calls_per_minute - len(recent_calls))


class APIUsageTracker:
    """Track API usage and estimate costs."""
    
    # Gemini API pricing (as of 2024)
    PRICING = {
        'gemini-1.5-flash': {
            'input': 0.075 / 1_000_000,      # $0.075 per 1M input tokens
            'output': 0.30 / 1_000_000,      # $0.30 per 1M output tokens
        },
        'gemini-2.0-flash': {
            'input': 0.10 / 1_000_000,
            'output': 0.40 / 1_000_000,
        }
    }
    
    def __init__(self):
        """Initialize usage tracker."""
        self.usage = defaultdict(lambda: {
            'calls': 0,
            'tokens_in': 0,
            'tokens_out': 0,
            'total_cost': 0.0
        })
        self.lock = Lock()
    
    def record_api_call(
        self,
        user_id: str,
        model: str,
        tokens_in: int,
        tokens_out: int
    ) -> float:
        """
        Record an API call and return cost.
        
        Args:
            user_id: User identifier
            model: Model name
            tokens_in: Input tokens used
            tokens_out: Output tokens used
        
        Returns:
            Cost of this call in USD
        """
        with self.lock:
            if model not in self.PRICING:
                logger.warning(f"Unknown model for pricing: {model}")
                return 0.0
            
            pricing = self.PRICING[model]
            call_cost = (
                tokens_in * pricing['input'] +
                tokens_out * pricing['output']
            )
            
            self.usage[user_id]['calls'] += 1
            self.usage[user_id]['tokens_in'] += tokens_in
            self.usage[user_id]['tokens_out'] += tokens_out
            self.usage[user_id]['total_cost'] += call_cost
            
            return call_cost
    
    def get_user_cost(self, user_id: str) -> float:
        """Get total cost for user."""
        with self.lock:
            return self.usage[user_id]['total_cost']
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get usage statistics for user."""
        with self.lock:
            stats = self.usage[user_id].copy()
            stats['average_cost_per_call'] = (
                stats['total_cost'] / stats['calls']
                if stats['calls'] > 0 else 0.0
            )
            return stats
    
    def check_quota(
        self,
        user_id: str,
        max_cost: float = 10.0
    ) -> Tuple[bool, Dict]:
        """
        Check if user is within cost quota.
        
        Args:
            user_id: User identifier
            max_cost: Maximum allowed monthly cost
        
        Returns:
            Tuple of (within_quota, quota_info_dict)
        """
        with self.lock:
            stats = self.usage[user_id]
            current_cost = stats['total_cost']
            remaining = max_cost - current_cost
            
            info = {
                'current_cost': current_cost,
                'max_cost': max_cost,
                'remaining': remaining,
                'api_calls': stats['calls'],
                'within_quota': remaining > 0,
                'usage_percent': (current_cost / max_cost * 100) if max_cost > 0 else 0
            }
            
            return remaining > 0, info


class QuotaEnforcer:
    """Enforce API quotas and prevent overspending."""
    
    def __init__(self, tracker: APIUsageTracker, default_monthly_limit: float = 10.0):
        """
        Initialize quota enforcer.
        
        Args:
            tracker: APIUsageTracker instance
            default_monthly_limit: Default monthly cost limit per user
        """
        self.tracker = tracker
        self.default_limit = default_monthly_limit
        self.user_limits = {}
        self.lock = Lock()
    
    def set_user_limit(self, user_id: str, monthly_limit: float):
        """Set custom monthly limit for user."""
        with self.lock:
            self.user_limits[user_id] = monthly_limit
    
    def check_quota_before_call(self, user_id: str) -> Tuple[bool, Dict]:
        """
        Check quota before allowing API call.
        
        Args:
            user_id: User identifier
        
        Returns:
            Tuple of (allowed, info_dict)
        """
        limit = self.user_limits.get(user_id, self.default_limit)
        allowed, info = self.tracker.check_quota(user_id, max_cost=limit)
        
        if not allowed:
            logger.warning(
                f"User {user_id} quota exceeded: "
                f"${info['current_cost']:.2f} of ${info['max_cost']:.2f}"
            )
        
        return allowed, info


if __name__ == "__main__":
    print("Testing rate limiting and usage tracking...\n")
    
    # Test rate limiter
    limiter = RateLimiter(calls_per_minute=3)
    
    print("Rate Limiter Test:")
    for i in range(5):
        allowed, wait_time = limiter.is_allowed("user_1")
        if allowed:
            print(f"  Call {i+1}: ✓ Allowed")
        else:
            print(f"  Call {i+1}: ✗ Rate limited (wait {wait_time:.1f}s)")
    
    print()
    
    # Test usage tracker
    tracker = APIUsageTracker()
    
    print("Usage Tracker Test:")
    cost1 = tracker.record_api_call("user_1", "gemini-1.5-flash", 1000, 500)
    print(f"  Call 1 cost: ${cost1:.4f}")
    
    cost2 = tracker.record_api_call("user_1", "gemini-1.5-flash", 2000, 1000)
    print(f"  Call 2 cost: ${cost2:.4f}")
    
    stats = tracker.get_user_stats("user_1")
    print(f"  User stats: {stats}")
    
    allowed, quota_info = tracker.check_quota("user_1", max_cost=5.0)
    print(f"  Within $5.00 quota: {allowed}")
    print(f"  Quota info: {quota_info}")
