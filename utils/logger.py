"""
Logging configuration and utilities
Provides structured logging for the entire application
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta


def setup_logger(name: str, level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with both console and file handlers
    """
    logger = logging.getLogger(name)
    
    # Don't add handlers if they already exist
    if logger.handlers:
        return logger
    
    # Set level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        try:
            # Create logs directory if it doesn't exist
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use rotating file handler to manage log file size
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        except Exception as e:
            logger.warning(f"Failed to setup file logging: {e}")
    
    return logger


class OperationLogger:
    """Context manager for logging operations with timing"""
    
    def __init__(self, logger: logging.Logger, operation: str, level: str = "INFO"):
        self.logger = logger
        self.operation = operation
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.log(self.level, f"Starting operation: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = datetime.utcnow() - self.start_time
        else:
            duration = timedelta(0)
        
        if exc_type is None:
            self.logger.log(
                self.level, 
                f"Completed operation: {self.operation} (duration: {duration.total_seconds():.2f}s)"
            )
        else:
            self.logger.error(
                f"Failed operation: {self.operation} (duration: {duration.total_seconds():.2f}s) - {exc_val}"
            )


class StructuredLogger:
    """Logger that supports structured logging with additional context"""
    
    def __init__(self, base_logger: logging.Logger):
        self.base_logger = base_logger
        self.context = {}
    
    def add_context(self, **kwargs):
        """Add context that will be included in all subsequent log messages"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear all context"""
        self.context.clear()
    
    def _format_message(self, message: str, **kwargs) -> str:
        """Format message with context and additional data"""
        all_context = {**self.context, **kwargs}
        
        if all_context:
            context_str = " | ".join([f"{k}={v}" for k, v in all_context.items()])
            return f"{message} | {context_str}"
        return message
    
    def debug(self, message: str, **kwargs):
        self.base_logger.debug(self._format_message(message, **kwargs))
    
    def info(self, message: str, **kwargs):
        self.base_logger.info(self._format_message(message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        self.base_logger.warning(self._format_message(message, **kwargs))
    
    def error(self, message: str, **kwargs):
        self.base_logger.error(self._format_message(message, **kwargs))
    
    def critical(self, message: str, **kwargs):
        self.base_logger.critical(self._format_message(message, **kwargs))


def create_operation_logger(logger: logging.Logger, operation: str, **context) -> StructuredLogger:
    """Create a structured logger for a specific operation"""
    structured_logger = StructuredLogger(logger)
    structured_logger.add_context(operation=operation, **context)
    return structured_logger


# Performance monitoring utilities
class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.operation_times = {}
        self.operation_counts = {}
    
    def record_operation(self, operation_name: str, duration: float):
        """Record the duration of an operation"""
        if operation_name not in self.operation_times:
            self.operation_times[operation_name] = []
            self.operation_counts[operation_name] = 0
        
        self.operation_times[operation_name].append(duration)
        self.operation_counts[operation_name] += 1
    
    def get_statistics(self) -> dict:
        """Get performance statistics"""
        stats = {}
        
        for operation, times in self.operation_times.items():
            if times:
                stats[operation] = {
                    "count": self.operation_counts[operation],
                    "total_time": sum(times),
                    "average_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times)
                }
        
        return stats
    
    def log_statistics(self):
        """Log current performance statistics"""
        stats = self.get_statistics()
        
        if stats:
            self.logger.info("Performance Statistics:")
            for operation, metrics in stats.items():
                self.logger.info(
                    f"  {operation}: count={metrics['count']}, "
                    f"avg={metrics['average_time']:.3f}s, "
                    f"min={metrics['min_time']:.3f}s, "
                    f"max={metrics['max_time']:.3f}s"
                )
        else:
            self.logger.info("No performance statistics available")
    
    def reset_statistics(self):
        """Reset all performance statistics"""
        self.operation_times.clear()
        self.operation_counts.clear()
        self.logger.info("Performance statistics reset")
