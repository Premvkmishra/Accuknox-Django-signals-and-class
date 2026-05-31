"""
Tests for Django signal threading behavior.

This module contains tests to investigate whether Django signals run
in the same thread as the caller.

Hypothesis: Django signals run in the same thread as the caller.
"""
import logging
import threading
from typing import Any

import pytest
from django.test import TestCase

from core.models import SignalTestModel
from core.signals import get_signal_execution_data, reset_signal_execution_data

logger = logging.getLogger(__name__)


class SignalThreadingTests(TestCase):
    """Test suite for investigating Django signal threading behavior."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        reset_signal_execution_data()
        SignalTestModel.objects.all().delete()

    def tearDown(self) -> None:
        """Clean up after tests."""
        SignalTestModel.objects.all().delete()
        reset_signal_execution_data()

    def test_signal_runs_in_same_thread_as_caller(self) -> None:
        """Test that Django signals run in the same thread as the caller.

        Method:
        1. Capture the caller's thread ID using threading.get_ident()
        2. Create a SignalTestModel instance
        3. The signal handler captures its thread ID
        4. Compare the thread IDs

        Expected:
        - Caller thread ID should equal signal thread ID
        - This proves signals run in the same thread
        """
        caller_thread_id = str(threading.get_ident())

        logger.info(
            "Starting same-thread test",
            extra={
                "test": "test_signal_runs_in_same_thread_as_caller",
                "caller_thread_id": caller_thread_id,
            },
        )

        instance = SignalTestModel.objects.create(
            name="thread_test",
            caller_thread_id=caller_thread_id,
            signal_delay_seconds=0.0,
        )

        # Reload to get signal-updated values
        instance.refresh_from_db()

        signal_thread_id = instance.signal_thread_id
        same_thread = caller_thread_id == signal_thread_id

        logger.info(
            "Same-thread test completed",
            extra={
                "test": "test_signal_runs_in_same_thread_as_caller",
                "caller_thread_id": caller_thread_id,
                "signal_thread_id": signal_thread_id,
                "same_thread": same_thread,
            },
        )

        # Assertions
        self.assertIsNotNone(signal_thread_id, "Signal thread ID should be recorded")
        self.assertEqual(
            caller_thread_id,
            signal_thread_id,
            "Signal should run in the same thread as the caller",
        )
        self.assertTrue(instance.signal_executed, "Signal should have been executed")

    def test_multiple_signals_run_in_same_thread(self) -> None:
        """Test that multiple signal invocations run in the same thread.

        Method:
        1. Create multiple instances sequentially
        2. Verify all signals run in the caller's thread

        Expected:
        - All signal thread IDs should match the caller thread ID
        """
        caller_thread_id = str(threading.get_ident())

        instances = []
        for i in range(5):
            instance = SignalTestModel.objects.create(
                name=f"thread_test_{i}",
                caller_thread_id=caller_thread_id,
                signal_delay_seconds=0.0,
            )
            instances.append(instance)

        # Reload all instances
        for instance in instances:
            instance.refresh_from_db()

        # Verify all signals ran in the same thread
        for i, instance in enumerate(instances):
            self.assertEqual(
                instance.caller_thread_id,
                caller_thread_id,
                f"Instance {i} caller thread ID should match",
            )
            self.assertEqual(
                instance.signal_thread_id,
                caller_thread_id,
                f"Instance {i} signal thread ID should match caller thread ID",
            )

        logger.info(
            "Multiple signals same-thread test passed",
            extra={
                "test": "test_multiple_signals_run_in_same_thread",
                "instance_count": len(instances),
                "caller_thread_id": caller_thread_id,
            },
        )

    def test_signal_thread_consistency_across_requests(self) -> None:
        """Test that signal thread behavior is consistent across multiple operations.

        Method:
        1. Perform multiple create operations
        2. Verify thread consistency for each

        Expected:
        - Each operation should maintain thread consistency
        """
        caller_thread_id = str(threading.get_ident())

        for iteration in range(3):
            instance = SignalTestModel.objects.create(
                name=f"consistency_test_{iteration}",
                caller_thread_id=caller_thread_id,
                signal_delay_seconds=0.0,
            )
            instance.refresh_from_db()

            self.assertEqual(
                instance.caller_thread_id,
                caller_thread_id,
                f"Iteration {iteration}: Caller thread ID should match",
            )
            self.assertEqual(
                instance.signal_thread_id,
                caller_thread_id,
                f"Iteration {iteration}: Signal thread ID should match caller",
            )

        logger.info(
            "Thread consistency test passed",
            extra={
                "test": "test_signal_thread_consistency_across_requests",
                "iterations": 3,
                "caller_thread_id": caller_thread_id,
            },
        )

    def test_signal_thread_id_is_valid(self) -> None:
        """Test that the captured signal thread ID is a valid thread identifier.

        Method:
        1. Create an instance
        2. Verify the signal thread ID is a valid thread ID format

        Expected:
        - Signal thread ID should be a non-empty string
        - Should be convertible to integer (thread IDs are numeric)
        """
        instance = SignalTestModel.objects.create(
            name="valid_thread_id_test",
            caller_thread_id=str(threading.get_ident()),
            signal_delay_seconds=0.0,
        )

        instance.refresh_from_db()

        signal_thread_id = instance.signal_thread_id

        # Assertions
        self.assertIsNotNone(signal_thread_id, "Signal thread ID should not be None")
        self.assertIsInstance(signal_thread_id, str, "Signal thread ID should be a string")
        self.assertTrue(len(signal_thread_id) > 0, "Signal thread ID should not be empty")

        # Thread IDs are typically numeric
        try:
            int(signal_thread_id)
        except ValueError:
            self.fail("Signal thread ID should be convertible to integer")

        logger.info(
            "Valid thread ID test passed",
            extra={
                "test": "test_signal_thread_id_is_valid",
                "signal_thread_id": signal_thread_id,
            },
        )

    def test_signal_in_different_caller_threads(self) -> None:
        """Test signal behavior when called from different threads.

        Method:
        1. Create instances from different threads
        2. Verify each signal runs in its respective caller thread

        Expected:
        - Each signal should run in the thread that called it
        """
        results: dict[str, Any] = {}
        lock = threading.Lock()

        def create_instance_in_thread(thread_name: str) -> None:
            """Create a SignalTestModel instance in a specific thread."""
            thread_id = str(threading.get_ident())
            instance = SignalTestModel.objects.create(
                name=f"thread_{thread_name}",
                caller_thread_id=thread_id,
                signal_delay_seconds=0.0,
            )
            instance.refresh_from_db()

            with lock:
                results[thread_name] = {
                    "caller_thread_id": thread_id,
                    "signal_thread_id": instance.signal_thread_id,
                    "same_thread": thread_id == instance.signal_thread_id,
                }

        # Create instances in different threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_instance_in_thread, args=(f"thread_{i}",))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify each signal ran in its caller's thread
        for thread_name, result in results.items():
            self.assertTrue(
                result["same_thread"],
                f"Signal in {thread_name} should run in the same thread as caller",
            )

        logger.info(
            "Different caller threads test passed",
            extra={
                "test": "test_signal_in_different_caller_threads",
                "results": results,
            },
        )

    def test_main_thread_signal_execution(self) -> None:
        """Test that signals run in the main thread when called from main thread.

        Method:
        1. Check if current thread is main thread
        2. Create instance
        3. Verify signal runs in main thread

        Expected:
        - If called from main thread, signal should run in main thread
        """
        is_main_thread = threading.current_thread() == threading.main_thread()
        caller_thread_id = str(threading.get_ident())

        instance = SignalTestModel.objects.create(
            name="main_thread_test",
            caller_thread_id=caller_thread_id,
            signal_delay_seconds=0.0,
        )

        instance.refresh_from_db()

        if is_main_thread:
            # Verify signal ran in main thread
            self.assertEqual(
                instance.signal_thread_id,
                caller_thread_id,
                "Signal should run in main thread when called from main thread",
            )

        logger.info(
            "Main thread test passed",
            extra={
                "test": "test_main_thread_signal_execution",
                "is_main_thread": is_main_thread,
                "caller_thread_id": caller_thread_id,
                "signal_thread_id": instance.signal_thread_id,
            },
        )


@pytest.mark.django_db
class SignalThreadingPytestTests:
    """Pytest-based tests for signal threading."""

    def test_signal_same_thread_pytest(self) -> None:
        """Test signal runs in same thread using pytest."""
        reset_signal_execution_data()
        caller_thread_id = str(threading.get_ident())

        instance = SignalTestModel.objects.create(
            name="pytest_thread_test",
            caller_thread_id=caller_thread_id,
            signal_delay_seconds=0.0,
        )

        instance.refresh_from_db()

        assert instance.signal_thread_id == caller_thread_id
        logger.info(
            "Pytest thread test passed",
            extra={
                "test": "test_signal_same_thread_pytest",
                "caller_thread_id": caller_thread_id,
                "signal_thread_id": instance.signal_thread_id,
            },
        )
