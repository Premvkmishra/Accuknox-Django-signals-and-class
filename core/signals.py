"""
Signal handlers for investigating Django signal behavior.

This module contains signal handlers used to investigate:
1. Synchronous vs asynchronous execution
2. Thread execution context
3. Transaction behavior

Each signal handler is designed to capture and log specific information
about signal execution behavior.
"""
import logging
import threading
import time
from typing import Any

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import SignalExecutionLog, SignalTestModel, TransactionTestModel

logger = logging.getLogger(__name__)


# Global storage for signal execution data (for testing purposes)
signal_execution_data: dict[str, Any] = {
    "caller_thread_id": None,
    "signal_thread_id": None,
    "execution_time": None,
    "executed": False,
}

# Track instances currently being processed to prevent recursion
_processing_instances: set[int] = set()


@receiver(post_save, sender=SignalTestModel)
def signal_test_handler(
    sender: type[SignalTestModel],
    instance: SignalTestModel,
    created: bool,
    **kwargs: Any,
) -> None:
    """Signal handler for testing synchronization and threading behavior.

    This handler:
    1. Captures the current thread ID
    2. Optionally introduces a delay (if specified in instance)
    3. Measures execution time
    4. Logs execution details

    Args:
        sender: The model class that sent the signal
        instance: The instance that was saved
        created: Whether this was a new instance
        **kwargs: Additional keyword arguments
    """
    global signal_execution_data, _processing_instances

    # Prevent recursive signal calls
    if instance.id in _processing_instances:
        return

    _processing_instances.add(instance.id)
    try:
        start_time = time.time()
        signal_thread_id = str(threading.get_ident())

        logger.info(
            "Signal handler started",
            extra={
                "signal_name": "signal_test_handler",
                "instance_id": instance.id,
                "signal_thread_id": signal_thread_id,
                "delay_seconds": instance.signal_delay_seconds,
            },
        )

        # Apply delay if specified
        if instance.signal_delay_seconds > 0:
            time.sleep(instance.signal_delay_seconds)

        # Update instance with signal execution data
        instance.signal_thread_id = signal_thread_id
        instance.signal_executed = True
        instance.signal_execution_time = time.time() - start_time
        instance.save(update_fields=["signal_thread_id", "signal_executed", "signal_execution_time"])

        # Store in global data for testing
        signal_execution_data["signal_thread_id"] = signal_thread_id
        signal_execution_data["execution_time"] = instance.signal_execution_time
        signal_execution_data["executed"] = True

        # Log execution details
        execution_time_ms = instance.signal_execution_time * 1000
        logger.info(
            "Signal handler completed",
            extra={
                "signal_name": "signal_test_handler",
                "instance_id": instance.id,
                "execution_time_ms": execution_time_ms,
                "signal_thread_id": signal_thread_id,
            },
        )
    finally:
        _processing_instances.discard(instance.id)


@receiver(post_save, sender=TransactionTestModel)
def transaction_test_handler(
    sender: type[TransactionTestModel],
    instance: TransactionTestModel,
    created: bool,
    **kwargs: Any,
) -> None:
    """Signal handler for testing transaction behavior.

    This handler:
    1. Creates a new TransactionTestModel instance
    2. Marks it as created in signal
    3. Tests whether it participates in the caller's transaction

    Args:
        sender: The model class that sent the signal
        instance: The instance that was saved
        created: Whether this was a new instance
        **kwargs: Additional keyword arguments
    """
    global _processing_instances

    # Prevent recursive signal calls
    # Skip if this instance was created by the signal handler itself
    if instance.created_in_signal:
        return

    if instance.id in _processing_instances:
        return

    _processing_instances.add(instance.id)
    try:
        signal_thread_id = str(threading.get_ident())

        logger.info(
            "Transaction signal handler started",
            extra={
                "signal_name": "transaction_test_handler",
                "instance_id": instance.id,
                "signal_thread_id": signal_thread_id,
                "in_transaction": transaction.get_autocommit() is False,
            },
        )

        # Create a new record within the signal
        # This will help determine if signals run in the same transaction
        signal_record = TransactionTestModel(
            name=f"{instance.name}_signal_created",
            created_in_signal=True,
        )
        signal_record.save()

        logger.info(
            "Transaction signal handler completed - created record",
            extra={
                "signal_name": "transaction_test_handler",
                "instance_id": instance.id,
                "signal_record_id": signal_record.id,
                "in_transaction": transaction.get_autocommit() is False,
            },
        )
    finally:
        _processing_instances.discard(instance.id)


def reset_signal_execution_data() -> None:
    """Reset global signal execution data.

    This function is used in tests to ensure a clean state between test runs.
    """
    global signal_execution_data, _processing_instances
    signal_execution_data = {
        "caller_thread_id": None,
        "signal_thread_id": None,
        "execution_time": None,
        "executed": False,
    }
    _processing_instances.clear()


def get_signal_execution_data() -> dict[str, Any]:
    """Get the current signal execution data.

    Returns:
        A dictionary containing signal execution information.
    """
    global signal_execution_data
    return signal_execution_data.copy()
