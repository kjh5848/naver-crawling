import time
from functools import wraps
from typing import Callable
import random

class RateLimiter:
    """요청 속도 제한"""
    
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0
        
    def wait(self):
        """요청 간 대기"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # 랜덤 지연 시간
        delay = random.uniform(self.min_delay, self.max_delay)
        
        if time_since_last < delay:
            time.sleep(delay - time_since_last)
            
        self.last_request_time = time.time()
        
def rate_limit(min_delay: float = 1.0, max_delay: float = 3.0):
    """데코레이터 방식 rate limiting"""
    def decorator(func: Callable):
        limiter = RateLimiter(min_delay, max_delay)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter.wait()
            return func(*args, **kwargs)
        return wrapper
    return decorator