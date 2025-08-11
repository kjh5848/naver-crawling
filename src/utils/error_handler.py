import time
from functools import wraps
from typing import Callable, Tuple, Type
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RetryHandler:
    """재시도 로직 처리"""
    
    @staticmethod
    def retry(
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """재시도 데코레이터"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                attempt = 1
                current_delay = delay
                
                while attempt <= max_attempts:
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        if attempt == max_attempts:
                            logger.error(f"Max attempts reached for {func.__name__}: {e}")
                            raise
                            
                        logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {current_delay}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                        attempt += 1
                        
            return wrapper
        return decorator