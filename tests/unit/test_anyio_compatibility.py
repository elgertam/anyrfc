"""
Test suite for AnyIO version compatibility.

This module specifically tests functionality that changed between AnyIO 4.5.1 and 4.6.0+
to ensure our codebase works correctly with the constrained version range.

Key areas tested:
- Task group cancellation behavior
- Lock/Semaphore performance and correctness
- Timeout handling with move_on_after
- State machine synchronization
"""

import anyio
import pytest
import time
import gc
import asyncio
import sys

# ExceptionGroup was introduced in Python 3.11
if sys.version_info >= (3, 11):
    import builtins

    _ExceptionGroup = getattr(builtins, "ExceptionGroup", Exception)
else:
    # For Python 3.9 and 3.10, we can use BaseExceptionGroup from exceptiongroup backport
    try:
        from exceptiongroup import ExceptionGroup as _ExceptionGroup
    except ImportError:
        # If backport not available, just use Exception as fallback
        _ExceptionGroup = Exception

from anyrfc.websocket.state_machine import WebSocketStateMachine, WSState, WSEvent


class TestTaskGroupCancellation:
    """Test task group cancellation behavior that was fixed in 4.6.0."""

    @pytest.mark.anyio
    async def test_task_group_cancellation_basic(self):
        """Test basic task group cancellation works correctly."""
        cancelled_tasks = []

        async def task1():
            try:
                await anyio.sleep(10)  # Long sleep
            except asyncio.CancelledError:
                cancelled_tasks.append("task1")
                raise

        async def task2():
            try:
                await anyio.sleep(10)  # Long sleep
            except asyncio.CancelledError:
                cancelled_tasks.append("task2")
                raise

        # Test cancellation via timeout
        with anyio.move_on_after(0.1):
            async with anyio.create_task_group() as tg:
                tg.start_soon(task1)
                tg.start_soon(task2)

        # Both tasks should have been cancelled
        assert "task1" in cancelled_tasks
        assert "task2" in cancelled_tasks

    @pytest.mark.anyio
    async def test_task_group_exception_propagation(self):
        """Test that exceptions properly propagate from task groups."""

        async def failing_task():
            await anyio.sleep(0.1)
            raise ValueError("Test error")

        async def normal_task():
            await anyio.sleep(1)  # Should be cancelled

        with pytest.raises((ValueError, _ExceptionGroup)):
            async with anyio.create_task_group() as tg:
                tg.start_soon(failing_task)
                tg.start_soon(normal_task)

    @pytest.mark.anyio
    async def test_nested_task_group_cancellation(self):
        """Test nested task group cancellation works correctly."""
        cancellation_order = []

        async def inner_task():
            try:
                await anyio.sleep(10)
            except asyncio.CancelledError:
                cancellation_order.append("inner")
                raise

        async def outer_task():
            try:
                async with anyio.create_task_group() as inner_tg:
                    inner_tg.start_soon(inner_task)
            except asyncio.CancelledError:
                cancellation_order.append("outer")
                raise

        with anyio.move_on_after(0.1):
            async with anyio.create_task_group() as tg:
                tg.start_soon(outer_task)

        assert "inner" in cancellation_order
        assert "outer" in cancellation_order


class TestLockSemaphorePerformance:
    """Test Lock and Semaphore behavior for performance regressions."""

    @pytest.mark.anyio
    async def test_lock_acquire_release_correctness(self):
        """Test that locks work correctly under concurrent access."""
        lock = anyio.Lock()
        counter = 0

        async def increment():
            nonlocal counter
            async with lock:
                # Simulate some work
                old_value = counter
                await anyio.sleep(0.01)
                counter = old_value + 1

        async with anyio.create_task_group() as tg:
            for _ in range(10):
                tg.start_soon(increment)

        assert counter == 10  # All increments should be atomic

    @pytest.mark.anyio
    async def test_lock_multiple_acquire_different_tasks(self):
        """Test that locks work correctly with multiple tasks."""
        lock = anyio.Lock()
        results = []

        async def task_with_lock(task_id: int):
            async with lock:
                results.append(f"start_{task_id}")
                await anyio.sleep(0.01)  # Hold lock briefly
                results.append(f"end_{task_id}")

        async with anyio.create_task_group() as tg:
            tg.start_soon(task_with_lock, 1)
            tg.start_soon(task_with_lock, 2)

        # Tasks should have run sequentially due to lock
        assert len(results) == 4
        # First task should complete before second starts
        assert results.index("end_1") < results.index("start_2") or results.index("end_2") < results.index("start_1")

    @pytest.mark.anyio
    async def test_semaphore_correctness(self):
        """Test semaphore behavior under concurrent access."""
        semaphore = anyio.Semaphore(2)  # Allow 2 concurrent tasks
        active_tasks = 0
        max_concurrent = 0

        async def limited_task():
            nonlocal active_tasks, max_concurrent
            async with semaphore:
                active_tasks += 1
                max_concurrent = max(max_concurrent, active_tasks)
                await anyio.sleep(0.1)  # Simulate work
                active_tasks -= 1

        async with anyio.create_task_group() as tg:
            for _ in range(5):
                tg.start_soon(limited_task)

        # Never more than 2 tasks should have been active simultaneously
        assert max_concurrent <= 2
        assert active_tasks == 0  # All tasks should be done


class TestTimeoutBehavior:
    """Test timeout behavior with move_on_after."""

    @pytest.mark.anyio
    async def test_move_on_after_accuracy(self):
        """Test that move_on_after timeouts are reasonably accurate."""
        start_time = time.time()

        with anyio.move_on_after(0.2) as cancel_scope:
            await anyio.sleep(1.0)  # This should be cancelled

        elapsed = time.time() - start_time

        # Should have been cancelled, not completed
        assert cancel_scope.cancelled_caught
        # Timing should be reasonably close (within 50ms tolerance)
        assert 0.15 <= elapsed <= 0.25

    @pytest.mark.anyio
    async def test_nested_timeout_behavior(self):
        """Test nested timeout scopes work correctly."""
        results = []

        with anyio.move_on_after(0.3) as outer_scope:  # Outer timeout
            results.append("outer_start")

            with anyio.move_on_after(0.1) as inner_scope:  # Inner timeout (shorter)
                results.append("inner_start")
                await anyio.sleep(0.2)  # Should be cancelled by inner scope
                results.append("inner_complete")  # Should not reach

            if inner_scope.cancelled_caught:
                results.append("inner_cancelled")

            await anyio.sleep(0.2)  # Should be cancelled by outer scope
            results.append("outer_complete")  # Should not reach

        assert "outer_start" in results
        assert "inner_start" in results
        assert "inner_cancelled" in results
        assert "inner_complete" not in results
        assert "outer_complete" not in results
        assert outer_scope.cancelled_caught


class TestStateMachineCompatibility:
    """Test our state machine implementation with AnyIO 4.5.1."""

    @pytest.mark.anyio
    async def test_state_machine_lock_behavior(self):
        """Test state machine synchronization works correctly."""
        sm = WebSocketStateMachine()

        state_changes = []

        async def state_changer():
            await sm.send_event(WSEvent.CONNECT)
            state_changes.append("connecting")
            await anyio.sleep(0.1)
            await sm.send_event(WSEvent.HANDSHAKE_COMPLETE)
            state_changes.append("open")

        async def state_waiter():
            await sm.wait_for_state(WSState.OPEN, timeout=1.0)
            state_changes.append("waited")

        async with anyio.create_task_group() as tg:
            tg.start_soon(state_changer)
            tg.start_soon(state_waiter)

        assert "connecting" in state_changes
        assert "open" in state_changes
        assert "waited" in state_changes
        assert sm.current_state == WSState.OPEN

    @pytest.mark.anyio
    async def test_concurrent_state_machine_access(self):
        """Test multiple tasks accessing state machine concurrently."""
        sm = WebSocketStateMachine()

        async def state_reader():
            # Just read the state repeatedly
            for _ in range(100):
                _ = sm.current_state
                await anyio.sleep(0.001)

        async def state_writer():
            # Change state through valid transitions
            await sm.send_event(WSEvent.CONNECT)
            await anyio.sleep(0.01)
            await sm.send_event(WSEvent.HANDSHAKE_COMPLETE)
            await anyio.sleep(0.01)
            # Can't easily trigger more transitions without going through full cycle

        # Should not deadlock or crash
        async with anyio.create_task_group() as tg:
            tg.start_soon(state_reader)
            tg.start_soon(state_reader)  # Multiple readers
            tg.start_soon(state_writer)


class TestMemoryUsage:
    """Test for memory leaks that could indicate task group issues."""

    @pytest.mark.anyio
    async def test_task_group_cleanup(self):
        """Test that task groups clean up properly and don't leak memory."""
        # Get initial object count
        gc.collect()
        initial_objects = len(gc.get_objects())

        async def create_many_task_groups():
            for _ in range(100):
                async with anyio.create_task_group() as tg:
                    tg.start_soon(anyio.sleep, 0.001)

        await create_many_task_groups()

        # Force garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())

        # Should not have significantly more objects (allow some variance)
        assert final_objects - initial_objects < 50

    @pytest.mark.anyio
    async def test_cancelled_task_cleanup(self):
        """Test that cancelled tasks clean up properly."""
        cancelled_count = 0

        async def cancellable_task():
            nonlocal cancelled_count
            try:
                await anyio.sleep(10)  # Will be cancelled
            except asyncio.CancelledError:
                cancelled_count += 1
                raise

        # Create and cancel many tasks
        for _ in range(50):
            with anyio.move_on_after(0.01):
                async with anyio.create_task_group() as tg:
                    tg.start_soon(cancellable_task)

        assert cancelled_count == 50


class TestRegressionScenarios:
    """Test specific scenarios that could reveal AnyIO 4.5.1 issues."""

    @pytest.mark.anyio
    async def test_connection_pattern_simulation(self):
        """Simulate our typical connection pattern with timeouts."""
        connection_states = []

        async def simulate_connection():
            connection_states.append("connecting")
            await anyio.sleep(0.1)  # Simulate connection time
            connection_states.append("connected")

            # Simulate some protocol work
            await anyio.sleep(0.1)
            connection_states.append("working")

            await anyio.sleep(0.1)
            connection_states.append("done")

        # Test with timeout that should succeed
        with anyio.move_on_after(1.0) as scope:
            await simulate_connection()

        assert not scope.cancelled_caught
        assert "done" in connection_states

        # Test with timeout that should cancel
        connection_states.clear()
        with anyio.move_on_after(0.05) as scope:
            await simulate_connection()

        assert scope.cancelled_caught
        assert "done" not in connection_states

    @pytest.mark.anyio
    async def test_websocket_style_state_machine_usage(self):
        """Test state machine usage pattern similar to our WebSocket client."""
        sm = WebSocketStateMachine()

        async def connection_manager():
            await sm.send_event(WSEvent.CONNECT)
            await anyio.sleep(0.1)  # Simulate connection
            await sm.send_event(WSEvent.HANDSHAKE_COMPLETE)
            await anyio.sleep(0.1)  # Simulate operation

        async def command_sender():
            # Wait for connection to be open
            await sm.wait_for_state(WSState.OPEN, timeout=1.0)
            # Send commands (simulated)
            for _ in range(5):
                await anyio.sleep(0.02)

        async def monitor():
            # Monitor state changes
            changes = []
            while sm.current_state != WSState.OPEN:
                changes.append(sm.current_state)
                await anyio.sleep(0.01)
            return changes

        async with anyio.create_task_group() as tg:
            tg.start_soon(connection_manager)
            tg.start_soon(command_sender)
            tg.start_soon(monitor)

        assert sm.current_state == WSState.OPEN
