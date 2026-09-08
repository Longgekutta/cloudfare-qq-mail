'''Simple in-memory sliding window rate limiting for Flask endpoints.'''

import threading
import time
from functools import wraps

from flask import render_template, request

DEFAULT_ERROR_MESSAGE = '请求过于频繁，请稍后再试'


def extract_client_ip():
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        candidate = forwarded.split(',')[0].strip()
        if candidate:
            return candidate
    return request.remote_addr or 'unknown'


class SimpleRateLimiter:
    '''Thread-safe sliding window limiter.'''

    def __init__(self, time_func=None):
        self._storage = {}
        self._lock = threading.Lock()
        self._time = time_func or time.time

    def is_allowed(self, key, max_requests, window_seconds):
        if max_requests <= 0:
            return False
        if window_seconds <= 0:
            return True
        now = self._time()
        window_start = now - window_seconds
        with self._lock:
            timestamps = [ts for ts in self._storage.get(key, []) if ts > window_start]
            allowed = len(timestamps) < max_requests
            if allowed:
                timestamps.append(now)
            if timestamps:
                self._storage[key] = timestamps
            else:
                self._storage.pop(key, None)
            return allowed


_default_limiter = SimpleRateLimiter()


def rate_limit(max_requests=5, window_seconds=60, methods=None, template_name='login.html', message=DEFAULT_ERROR_MESSAGE, limiter=None):
    target_methods = {str(item).upper() for item in (methods or ('POST',))}
    active_limiter = limiter or _default_limiter

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if request.method.upper() in target_methods:
                client_ip = extract_client_ip()
                if not active_limiter.is_allowed(client_ip, max_requests, window_seconds):
                    return render_template(template_name, error=message), 429
            return func(*args, **kwargs)
        return wrapper

    return decorator
