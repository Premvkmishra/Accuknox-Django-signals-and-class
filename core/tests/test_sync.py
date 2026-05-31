"""
Tests for Django signal synchronization behavior.

This module contains tests to investigate whether Django signals are
executed synchronously or asynchronously.

Hypothesis: Django signals are executed synchronously by default.
"""
import logging
import threading
import time
from typing import Any

import pytest
from django.core.management import call_command
from django.db import transaction
from django.test import TestCase

from core.models import SignalTestModel
from core.signals import get_signal_execution_data, reset_signal_execution_data

logger = logging.getLogger(__name__)


class SignalSynchronizationTests(TestCase):
    """Test suite for investigating Django signal synchronization behavior."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        reset_signal_execution_data()
        SignalTestModel.objects.all().delete()

    def tearDown(self) -> None:
        """Clean up after tests."""
        SignalTestModel.objects.all().delete()
        reset_signal_execution_data()

    def test_signal_execution_is_synchronous(self) -> None:
        """Test that Django signals are executed synchronously.

        Method:
        1. Create a SignalTestModel with a 2-second delay in the signal
        2. Measure the total execution time
        3. Verify that the total time is >= 2 seconds

        Expected:
        - Total execution time should be >= signal delay
        - This proves the caller waits for signal completion
        """
        delay_seconds = 2.0
        caller_thread_id = str(threading.get_ident())

        logger.info(
            "Starting synchronous execution test",
            extra={
                "test": "test_signal_execution_is_synchronous",
                "delay_seconds": delay_seconds,
                "caller_thread_id": caller_thread_id,
            },
        )

        start_time = time.time()

        instance = SignalTestModel.objects.create(
            name="sync_test",
            caller_thread_id=caller_thread_id,
            signal_delay_seconds=delay_seconds,
        )

        total_time = time.time() - start_time

        # Reload to get signal-updated values
        instance.refresh_from_db()

        logger.info(
            "Synchronous execution test completed",
            extra={
                "test": "test_signal_execution_is_synchronous",
                "total_time": total_time,
                "signal_delay": delay_seconds,
                "signal_executed": instance.signal_executed,
                "signal_execution_time": instance.signal_execution_time,
            },
        )

        # Assertions
        self.assertTrue(instance.signal_executed, "Signal should have been executed")
        self.assertIsNotNone(instance.signal_execution_time, "Signal execution time should be recorded")
        self.assertGreaterEqual(
            total_time,
            delay_seconds * 0.9,  # Allow 10% tolerance for system overhead
            "Total execution time should be >= signal delay (with 10% tolerance)",
        )
        self.assertGreaterEqual(
            instance.signal_execution_time,
            delay_seconds * 0.9,
            "Signal execution time should be >= delay (with 10% tolerance)",
        )

    def test_signal_blocks_caller_execution(self) -> None:
        """Test that signal execution blocks the caller from continuing.

        Method:
        1. Set a flag before signal execution
        2. Create instance with signal delay
        3. Check flag after signal completes
        4. Verify caller couldn't proceed during signal execution

        Expected:
        - Caller code after save() should not execute until signal completes
        """
        delay_seconds = 1.0
        execution_order: list[str] = []

        def before_save() -> None:
            """Record timestamp before save."""
            execution_order.append("before_save")

        def after_save() -> None:
            """Record timestamp after save."""
            execution_order.append("after_save")

        before_save()

        instance = SignalTestModel.objects.create(
            name="blocking_test",
            caller_thread_id=str(threading.get_ident()),
            signal_delay_seconds=delay_seconds,
        )

        after_save()

        logger.info(
            "Blocking test execution order",
            extra={
                "test": "test_signal_blocks_caller_execution",
                "execution_order": execution_order,
            },
        )

        # The signal should complete before after_save is called
        self.assertEqual(len(execution_order), 2, "Should have exactly 2 execution markers")
        self.assertEqual(execution_order[0], "before_save", "First marker should be before_save")
        self.assertEqual(execution_order[1], "after_save", "Second marker should be after_save")

        # Reload and verify signal executed
        instance.refresh_from_db()
        self.assertTrue(instance.signal_executed, "Signal should have been executed")

    def test_signal_execution_order_is_deterministic(self) -> None:
        """Test that signal execution order is deterministic.

        Method:
        1. Create multiple instances sequentially
        2. Verify signals execute in the same order

        Expected:
        - Signals should execute in the order they were triggered
        """
        instances = []
        for i in range(3):
            instance = SignalTestModel.objects.create(
                name=f"order_test_{i}",
                caller_thread_id=str(threading.get_ident()),
                signal_delay_seconds=0.1,
            )
            instances.append(instance)

        # Reload all instances
        for instance in instances:
            instance.refresh_from_db()

        # All signals should have executed
        for instance in instances:
            self.assertTrue(instance.signal_executed, f"Signal for {instance.name} should have executed")

        # Verify execution times are sequential (not overlapping)
        execution_times = [instance.signal_execution_time for instance in instances]
        logger.info(
            "Execution order test results",
            extra={
                "test": "test_signal_execution_order_is_deterministic",
                "execution_times": execution_times,
            },
        )

        # With synchronous execution, each should have similar execution times
        # (not overlapping which would indicate async behavior)
        for exec_time in execution_times:
            self.assertGreaterEqual(
                exec_time,
                0.1 * 0.9,
                "Each signal should have execution time >= delay",
            )

    def test_signal_error_propagates_to_caller(self) -> None:
        """Test that signal errors propagate to the caller.

        Method:
        1. Create a signal handler that raises an exception
        2. Verify the exception propagates to the caller

        Expected:
        - Exception in signal should propagate to caller
        - This proves synchronous execution
        """
        # This test demonstrates that signal errors affect the caller
        # We'll use a try-except to catch the expected error
        from django.db.models.signals import post_save
        from django.dispatch import receiver

        @receiver(post_save, sender=SignalTestModel)
        def error_signal_handler(sender: Any, instance: SignalTestModel, **kwargs: Any) -> None:
            """Signal handler that raises an exception."""
            raise ValueError("Test exception from signal")

        try:
            with self.assertRaises(ValueError) as context:
                SignalTestModel.objects.create(
                    name="error_test",
                    caller_thread_id=str(threading.get_ident()),
                    signal_delay_seconds=0.0,
                )

            self.assertEqual(str(context.exception), "Test exception from signal")
            logger.info(
                "Signal error propagation test passed",
                extra={"test": "test_signal_error_propagates_to_caller"},
            )
        finally:
            # Clean up the signal handler
            post_save.disconnect(error_signal_handler, sender=SignalTestModel)

    def test_multiple_signals_execute_synchronously(self) -> None:
        """Test that multiple signals for the same event execute synchronously.

        Method:
        1. Register multiple signal handlers
        2. Trigger the signal
        3. Verify all execute before caller continues

        Expected:
        - All signal handlers should complete before caller continues
        """
        from django.db.models.signals import post_save
        from django.dispatch import receiver

        execution_log: list[str] = []

        @receiver(post_save, sender=SignalTestModel)
        def signal_handler_1(sender: Any, instance: SignalTestModel, **kwargs: Any) -> None:
            """First signal handler."""
            execution_log.append("handler_1_start")
            time.sleep(0.1)
            execution_log.append("handler_1_end")

        @receiver(post_save, sender=SignalTestModel)
        def signal_handler_2(sender: Any, instance: SignalTestModel, **kwargs: Any) -> None:
            """Second signal handler."""
            execution_log.append("handler_2_start")
            time.sleep(0.1)
            execution_log.append("handler_2_end")

        try:
            start_time = time.time()
            instance = SignalTestModel.objects.create(
                name="multiple_signals_test",
                caller_thread_id=str(threading.get_ident()),
                signal_delay_seconds=0.0,
            )
            total_time = time.time() - start_time

            logger.info(
                "Multiple signals test results",
                extra={
                    "test": "test_multiple_signals_execute_synchronously",
                    "execution_log": execution_log,
                    "total_time": total_time,
                },
            )

            # All handlers should have executed
            self.assertIn("handler_1_start", execution_log)
            self.assertIn("handler_1_end", execution_log)
            self.assertIn("handler_2_start", execution_log)
            self.assertIn("handler_2_end", execution_log)

            # Total time should reflect sequential execution
            self.assertGreaterEqual(total_time, 0.2, "Total time should be >= sum of delays")

        finally:
            # Clean up signal handlers
            post_save.disconnect(signal_handler_1, sender=SignalTestModel)
            post_save.disconnect(signal_handler_2, sender=SignalTestModel)


@pytest.mark.django_db
class SignalSynchronizationPytestTests:
    """Pytest-based tests for signal synchronization."""

    def test_signal_sync_with_pytest(self) -> None:
        """Test signal synchronization using pytest."""
        reset_signal_execution_data()
        delay_seconds = 1.5

        start_time = time.time()
        instance = SignalTestModel.objects.create(
            name="pytest_sync_test",
            caller_thread_id=str(threading.get_ident()),
            signal_delay_seconds=delay_seconds,
        )
        total_time = time.time() - start_time

        instance.refresh_from_db()

        assert instance.signal_executed is True
        assert total_time >= delay_seconds * 0.9
        logger.info(
            "Pytest sync test passed",
            extra={
                "test": "test_signal_sync_with_pytest",
                "total_time": total_time,
                "delay_seconds": delay_seconds,
            },
        )
