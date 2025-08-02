"""
Retry utilities for handling transient failures
Provides decorators and functions for retry logic
"""

import asyncio
import functools
import random
from typing import Callable, Any, Optional, Union, Type
from datetime import datetime, timedelta

from utils.logger import setup_logger


def retry_async(max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0,
                exceptions: Union[Type[Exception], tuple] = Exception,
                jitter: bool = True) -> Callable:
    """
    Async retry decorator with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Factor by which delay increases after each retry
        exceptions: Exception types to catch and retry on
        jitter: Whether to add random jitter to delay
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            logger = setup_logger(f"retry.{func.__name__}")
            
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    
                    if attempt > 0:
                        logger.info(f"Operation succeeded after {attempt} retries")
                    
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Operation failed after {max_retries} retries: {str(e)}")
                        raise e
                    
                    # Calculate delay with optional jitter
                    actual_delay = current_delay
                    if jitter:
                        actual_delay *= (0.5 + random.random())
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {str(e)}. "
                        f"Retrying in {actual_delay:.2f} seconds..."
                    )
                    
                    await asyncio.sleep(actual_delay)
                    current_delay *= backoff_factor
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            else:
                raise Exception("Retry failed with no exception recorded")
        
        return wrapper
    return decorator


def retry_sync(max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0,
               exceptions: Union[Type[Exception], tuple] = Exception,
               jitter: bool = True) -> Callable:
    """
    Synchronous retry decorator with exponential backoff
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import time
            logger = setup_logger(f"retry.{func.__name__}")
            
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    if attempt > 0:
                        logger.info(f"Operation succeeded after {attempt} retries")
                    
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Operation failed after {max_retries} retries: {str(e)}")
                        raise e
                    
                    # Calculate delay with optional jitter
                    actual_delay = current_delay
                    if jitter:
                        actual_delay *= (0.5 + random.random())
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {str(e)}. "
                        f"Retrying in {actual_delay:.2f} seconds..."
                    )
                    
                    time.sleep(actual_delay)
                    current_delay *= backoff_factor
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            else:
                raise Exception("Retry failed with no exception recorded")
        
        return wrapper
    return decorator


class RetryManager:
    """Advanced retry manager with circuit breaker functionality"""
    
    def __init__(self, name: str, failure_threshold: int = 5, 
                 recovery_timeout: float = 60.0, half_open_max_calls: int = 3):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half_open
        self.half_open_calls = 0
        
        self.logger = setup_logger(f"retry_manager.{name}")
    
    async def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker logic"""
        
        # Check circuit breaker state
        if self.state == "open":
            if self._should_attempt_reset():
                self._set_half_open()
            else:
                raise Exception(f"Circuit breaker is open for {self.name}")
        
        if self.state == "half_open" and self.half_open_calls >= self.half_open_max_calls:
            raise Exception(f"Circuit breaker half-open limit exceeded for {self.name}")
        
        try:
            if self.state == "half_open":
                self.half_open_calls += 1
            
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success - reset failure count and close circuit if needed
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = datetime.utcnow() - self.last_failure_time
        return time_since_failure >= timedelta(seconds=self.recovery_timeout)
    
    def _set_half_open(self):
        """Set circuit breaker to half-open state"""
        self.state = "half_open"
        self.half_open_calls = 0
        self.logger.info(f"Circuit breaker for {self.name} set to half-open")
    
    def _on_success(self):
        """Handle successful execution"""
        if self.state == "half_open":
            self._close_circuit()
        elif self.failure_count > 0:
            self.failure_count = 0
            self.logger.info(f"Reset failure count for {self.name}")
    
    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.state == "half_open":
            self._open_circuit()
        elif self.failure_count >= self.failure_threshold:
            self._open_circuit()
        
        self.logger.warning(f"Failure recorded for {self.name} (count: {self.failure_count})")
    
    def _open_circuit(self):
        """Open the circuit breaker"""
        self.state = "open"
        self.half_open_calls = 0
        self.logger.error(f"Circuit breaker opened for {self.name}")
    
    def _close_circuit(self):
        """Close the circuit breaker"""
        self.state = "closed"
        self.failure_count = 0
        self.half_open_calls = 0
        self.last_failure_time = None
        self.logger.info(f"Circuit breaker closed for {self.name}")
    
    def get_status(self) -> dict:
        """Get current status of the circuit breaker"""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "half_open_calls": self.half_open_calls
        }


# Global retry managers for common operations
DATABASE_RETRY_MANAGER = RetryManager("database")
API_RETRY_MANAGER = RetryManager("api")
FILE_RETRY_MANAGER = RetryManager("file_operations")


async def execute_with_retry_manager(manager: RetryManager, func: Callable, *args, **kwargs) -> Any:
    """Execute a function using a specific retry manager"""
    return await manager.execute_async(func, *args, **kwargs)
