"""Tests for AnyIO compatibility layer."""

import pytest
import anyio
import sys
from anyrfc.core.anyio_compat import (
    HAS_NATIVE_EXCEPTION_GROUPS,
    HAS_ANYIO_OWN_EXCEPTION_GROUP,
    CancelledError,
    get_exception_group_types,
)


class TestAnyIOCompat:
    """Test the AnyIO compatibility layer."""

    def test_feature_flags(self):
        """Test that feature flags are correctly detected."""
        assert isinstance(HAS_NATIVE_EXCEPTION_GROUPS, bool)
        assert isinstance(HAS_ANYIO_OWN_EXCEPTION_GROUP, bool)

        # Should match Python version
        assert HAS_NATIVE_EXCEPTION_GROUPS == (sys.version_info >= (3, 11))

    def test_exception_group_types(self):
        """Test that exception group types are detected correctly."""
        exception_types = get_exception_group_types()
        assert isinstance(exception_types, tuple)
        assert len(exception_types) >= 1
        # All types should be exception classes (BaseException or Exception)
        for exc_type in exception_types:
            assert issubclass(exc_type, BaseException)

    def test_cancellation_exception(self):
        """Test that cancellation exception is correct."""
        # CancelledError should be the standard asyncio exception
        import asyncio

        assert CancelledError is asyncio.CancelledError

    @pytest.mark.anyio
    async def test_exception_handling_compatibility(self):
        """Test that exception handling works across AnyIO versions."""
        exception_types = get_exception_group_types()

        async def failing_task():
            await anyio.sleep(0.01)
            raise ValueError("Test error")

        async def normal_task():
            await anyio.sleep(0.1)

        # This should work regardless of AnyIO version
        with pytest.raises((ValueError, *exception_types)):
            async with anyio.create_task_group() as tg:
                tg.start_soon(failing_task)
                tg.start_soon(normal_task)

    @pytest.mark.anyio
    async def test_cancellation_handling(self):
        """Test that cancellation works correctly."""
        cancelled_tasks = []

        async def cancellable_task():
            try:
                await anyio.sleep(10)
            except CancelledError:
                cancelled_tasks.append("cancelled")
                raise

        with anyio.move_on_after(0.1):
            async with anyio.create_task_group() as tg:
                tg.start_soon(cancellable_task)

        assert "cancelled" in cancelled_tasks
