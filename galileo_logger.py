#!/usr/bin/env python3
"""
Centralized Galileo Logger for the application.
This ensures we have a single GalileoLogger instance shared across all components.
"""

import os
from dotenv import load_dotenv
from galileo import GalileoLogger

# Load environment variables
load_dotenv()

# Global Galileo logger instance
_galileo_logger = None

def get_galileo_logger():
    """
    Get the global Galileo logger instance.
    Creates it if it doesn't exist.
    """
    global _galileo_logger
    
    if _galileo_logger is None:
        try:
            project = os.environ.get("GALILEO_PROJECT")
            log_stream = os.environ.get("GALILEO_LOG_STREAM")
            api_key = os.environ.get("GALILEO_API_KEY")
            
            if not api_key:
                print("⚠️  Warning: GALILEO_API_KEY not set. Galileo logging will be disabled.")
                return None
            
            if not project or not log_stream:
                print("⚠️  Warning: GALILEO_PROJECT or GALILEO_LOG_STREAM not set. Galileo logging will be disabled.")
                return None
            
            _galileo_logger = GalileoLogger(project=project, log_stream=log_stream)
            print(f"✅ Galileo logger initialized for project: {project}, stream: {log_stream}")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize Galileo logger: {e}")
            print("   Galileo logging will be disabled.")
            return None
    
    return _galileo_logger

def safe_galileo_operation(operation_func, *args, **kwargs):
    """
    Safely execute a Galileo operation with error handling.
    
    Args:
        operation_func: Function to execute (e.g., logger.start_trace)
        *args, **kwargs: Arguments to pass to the function
    
    Returns:
        Result of the operation, or None if it fails
    """
    logger = get_galileo_logger()
    if logger is None:
        return None
    
    try:
        return operation_func(*args, **kwargs)
    except Exception as e:
        print(f"⚠️  Galileo operation failed: {e}")
        return None

# Convenience functions for common operations
def start_trace(name):
    """Start a Galileo trace safely."""
    logger = get_galileo_logger()
    if logger is None:
        return None
    return safe_galileo_operation(logger.start_trace, name)

def add_llm_span(**kwargs):
    """Add an LLM span safely."""
    logger = get_galileo_logger()
    if logger is None:
        return None
    return safe_galileo_operation(logger.add_llm_span, **kwargs)

def conclude_trace(output, duration_ns=0, error=False):
    """Conclude a trace safely."""
    logger = get_galileo_logger()
    if logger is None:
        return None
    return safe_galileo_operation(logger.conclude, output, duration_ns=duration_ns, error=error)

def flush_logger():
    """Flush the logger safely."""
    logger = get_galileo_logger()
    if logger is None:
        return None
    return safe_galileo_operation(logger.flush) 