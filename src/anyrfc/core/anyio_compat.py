"""
AnyIO compatibility layer using C-style feature flags.

This module provides feature detection for AnyIO capabilities,
allowing the codebase to work with different AnyIO versions
using conditional imports and feature flags.
"""

import sys
import asyncio
from typing import Type, Tuple

# Feature flags - detected at import time
HAS_NATIVE_EXCEPTION_GROUPS = sys.version_info >= (3, 11)
HAS_ANYIO_OWN_EXCEPTION_GROUP = False

# Try to detect AnyIO's own ExceptionGroup (4.5.x and earlier)
try:
    from anyio import ExceptionGroup as AnyIOExceptionGroup

    HAS_ANYIO_OWN_EXCEPTION_GROUP = True
except ImportError:
    AnyIOExceptionGroup = Exception

# Import standard exception groups (Python 3.11+ or backport)
if HAS_NATIVE_EXCEPTION_GROUPS:
    import builtins

    ExceptionGroup = getattr(builtins, "ExceptionGroup", Exception)
    BaseExceptionGroup = getattr(builtins, "BaseExceptionGroup", Exception)
else:
    # Use exceptiongroup backport for Python 3.9/3.10
    try:
        from exceptiongroup import ExceptionGroup, BaseExceptionGroup
    except ImportError:
        # Fallback if backport not available
        ExceptionGroup = Exception
        BaseExceptionGroup = Exception

# Cancellation exception (same across all versions)
CancelledError = asyncio.CancelledError


def get_exception_group_types() -> Tuple[Type[Exception], ...]:
    """Get exception types that task groups might raise."""
    if HAS_ANYIO_OWN_EXCEPTION_GROUP:
        # Old AnyIO with its own ExceptionGroup
        return (AnyIOExceptionGroup, ExceptionGroup, BaseExceptionGroup)
    else:
        # New AnyIO with standard exception groups
        return (ExceptionGroup, BaseExceptionGroup)


# Exports for use in the codebase
__all__ = [
    "HAS_NATIVE_EXCEPTION_GROUPS",
    "HAS_ANYIO_OWN_EXCEPTION_GROUP",
    "ExceptionGroup",
    "BaseExceptionGroup",
    "AnyIOExceptionGroup",
    "CancelledError",
    "get_exception_group_types",
]
