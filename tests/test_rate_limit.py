import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rate_limit import SimpleRateLimiter


def test_rate_limiter_allows_within_limit():
    current = [1000.0]
    limiter = SimpleRateLimiter(time_func=lambda: current[0])
    assert limiter.is_allowed('1.2.3.4', 3, 60) is True
    assert limiter.is_allowed('1.2.3.4', 3, 60) is True
    assert limiter.is_allowed('1.2.3.4', 3, 60) is True
    assert limiter.is_allowed('1.2.3.4', 3, 60) is False


def test_rate_limiter_window_expiry():
    current = [1000.0]
    limiter = SimpleRateLimiter(time_func=lambda: current[0])
    assert limiter.is_allowed('ip', 2, 60) is True
    assert limiter.is_allowed('ip', 2, 60) is True
    assert limiter.is_allowed('ip', 2, 60) is False
    current[0] += 61
    assert limiter.is_allowed('ip', 2, 60) is True


def test_rate_limiter_isolates_keys():
    limiter = SimpleRateLimiter(time_func=lambda: 1000.0)
    assert limiter.is_allowed('a', 1, 60) is True
    assert limiter.is_allowed('b', 1, 60) is True
    assert limiter.is_allowed('a', 1, 60) is False
