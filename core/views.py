"""
API views for signal investigation endpoints.

This module contains Django REST Framework views that provide endpoints
for investigating Django signal behavior, including synchronization,
threading, and transaction characteristics.
"""
import logging
import threading
import time
from typing import Any

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.models import SignalTestModel, TransactionTestModel
from core.signals import get_signal_execution_data, reset_signal_execution_data

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def signal_sync_test(request: Any) -> Response:
    """Test whether Django signals are executed synchronously.

    This endpoint:
    1. Creates a SignalTestModel with a delay
    2. Measures total execution time
    3. Compares with expected delay
    4. Returns evidence of synchronous execution

    Returns:
        Response containing timing data and conclusion.
    """
    reset_signal_execution_data()

    delay_seconds = 2.0
    caller_thread_id = str(threading.get_ident())

    logger.info(
        "Starting sync test",
        extra={
            "endpoint": "signal_sync_test",
            "caller_thread_id": caller_thread_id,
            "delay_seconds": delay_seconds,
        },
    )

    start_time = time.time()

    # Create instance with delay in signal
    instance = SignalTestModel.objects.create(
        name="sync_test",
        caller_thread_id=caller_thread_id,
        signal_delay_seconds=delay_seconds,
    )

    # Reload to get signal-updated values
    instance.refresh_from_db()

    total_time = time.time() - start_time
    signal_data = get_signal_execution_data()

    # Signal is synchronous if total time >= delay
    is_synchronous = total_time >= delay_seconds * 0.9  # Allow 10% tolerance

    logger.info(
        "Sync test completed",
        extra={
            "endpoint": "signal_sync_test",
            "total_time": total_time,
            "signal_delay": delay_seconds,
            "is_synchronous": is_synchronous,
        },
    )

    return Response(
        {
            "test": "signal_synchronization",
            "hypothesis": "Django signals are executed synchronously",
            "method": "Measure execution time with intentional signal delay",
            "results": {
                "caller_thread_id": caller_thread_id,
                "signal_thread_id": instance.signal_thread_id,
                "signal_delay_seconds": delay_seconds,
                "signal_execution_time": instance.signal_execution_time,
                "total_execution_time": total_time,
                "signal_executed": instance.signal_executed,
            },
            "conclusion": {
                "is_synchronous": is_synchronous,
                "explanation": (
                    f"Total execution time ({total_time:.2f}s) "
                    f"is {'greater than or equal to' if is_synchronous else 'less than'} "
                    f"the signal delay ({delay_seconds}s), indicating "
                    f"{'synchronous' if is_synchronous else 'asynchronous'} execution."
                ),
            },
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def signal_thread_test(request: Any) -> Response:
    """Test whether Django signals run in the same thread as the caller.

    This endpoint:
    1. Captures the caller's thread ID
    2. Creates a SignalTestModel
    3. Captures the signal handler's thread ID
    4. Compares the thread IDs

    Returns:
        Response containing thread ID comparison and conclusion.
    """
    reset_signal_execution_data()

    caller_thread_id = str(threading.get_ident())

    logger.info(
        "Starting thread test",
        extra={
            "endpoint": "signal_thread_test",
            "caller_thread_id": caller_thread_id,
        },
    )

    # Create instance
    instance = SignalTestModel.objects.create(
        name="thread_test",
        caller_thread_id=caller_thread_id,
        signal_delay_seconds=0.0,  # No delay for thread test
    )

    # Reload to get signal-updated values
    instance.refresh_from_db()

    signal_thread_id = instance.signal_thread_id
    same_thread = caller_thread_id == signal_thread_id

    logger.info(
        "Thread test completed",
        extra={
            "endpoint": "signal_thread_test",
            "caller_thread_id": caller_thread_id,
            "signal_thread_id": signal_thread_id,
            "same_thread": same_thread,
        },
    )

    return Response(
        {
            "test": "signal_threading",
            "hypothesis": "Django signals run in the same thread as the caller",
            "method": "Compare thread IDs of caller and signal handler",
            "results": {
                "caller_thread_id": caller_thread_id,
                "signal_thread_id": signal_thread_id,
                "same_thread": same_thread,
            },
            "conclusion": {
                "same_thread": same_thread,
                "explanation": (
                    f"Caller thread ID ({caller_thread_id}) is "
                    f"{'equal to' if same_thread else 'different from'} "
                    f"signal thread ID ({signal_thread_id}), indicating "
                    f"signals run in the {'same' if same_thread else 'different'} thread."
                ),
            },
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def signal_transaction_test(request: Any) -> Response:
    """Test whether Django signals run in the same database transaction.

    This endpoint:
    1. Creates a TransactionTestModel within a transaction
    2. The signal handler creates another TransactionTestModel
    3. Forces a rollback
    4. Checks if both records are rolled back

    Returns:
        Response containing transaction behavior and conclusion.
    """
    caller_thread_id = str(threading.get_ident())

    logger.info(
        "Starting transaction test",
        extra={
            "endpoint": "signal_transaction_test",
            "caller_thread_id": caller_thread_id,
        },
    )

    # Clear any existing records
    TransactionTestModel.objects.all().delete()

    try:
        with transaction.atomic():
            # Create initial record
            caller_record = TransactionTestModel.objects.create(
                name="transaction_test_caller",
                created_in_signal=False,
            )

            logger.info(
                "Created caller record in transaction",
                extra={
                    "endpoint": "signal_transaction_test",
                    "caller_record_id": caller_record.id,
                },
            )

            # Signal will create a second record
            # Force rollback
            raise Exception("Intentional rollback for testing")

    except Exception:
        # Expected exception for rollback
        pass

    # Check if records exist after rollback
    remaining_records = list(TransactionTestModel.objects.all())
    both_rolled_back = len(remaining_records) == 0

    logger.info(
        "Transaction test completed",
        extra={
            "endpoint": "signal_transaction_test",
            "remaining_records": len(remaining_records),
            "both_rolled_back": both_rolled_back,
        },
    )

    return Response(
        {
            "test": "signal_transaction",
            "hypothesis": "Django signals run in the same database transaction as the caller",
            "method": (
                "Create record in transaction, signal creates second record, "
                "force rollback, check if both records disappear"
            ),
            "results": {
                "caller_thread_id": caller_thread_id,
                "transaction_rolled_back": True,
                "remaining_records_count": len(remaining_records),
                "remaining_records": [
                    {"id": r.id, "name": r.name, "created_in_signal": r.created_in_signal}
                    for r in remaining_records
                ],
            },
            "conclusion": {
                "same_transaction": both_rolled_back,
                "explanation": (
                    f"After transaction rollback, {len(remaining_records)} record(s) remain. "
                    f"{'Both' if both_rolled_back else 'Not both'} records were rolled back, "
                    f"indicating signals {'do' if both_rolled_back else 'do not'} "
                    f"run in the same transaction as the caller."
                ),
            },
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def signal_transaction_commit_test(request: Any) -> Response:
    """Test signal behavior when transaction is committed.

    This endpoint:
    1. Creates a TransactionTestModel within a transaction
    2. The signal handler creates another TransactionTestModel
    3. Commits the transaction
    4. Checks if both records are persisted

    Returns:
        Response containing transaction commit behavior and conclusion.
    """
    caller_thread_id = str(threading.get_ident())

    logger.info(
        "Starting transaction commit test",
        extra={
            "endpoint": "signal_transaction_commit_test",
            "caller_thread_id": caller_thread_id,
        },
    )

    # Clear any existing records
    TransactionTestModel.objects.all().delete()

    with transaction.atomic():
        # Create initial record
        caller_record = TransactionTestModel.objects.create(
            name="transaction_commit_test_caller",
            created_in_signal=False,
        )

        logger.info(
            "Created caller record in transaction",
            extra={
                "endpoint": "signal_transaction_commit_test",
                "caller_record_id": caller_record.id,
            },
        )

        # Signal will create a second record
        # Transaction commits automatically

    # Check if records exist after commit
    remaining_records = list(TransactionTestModel.objects.all())
    both_persisted = len(remaining_records) == 2

    logger.info(
        "Transaction commit test completed",
        extra={
            "endpoint": "signal_transaction_commit_test",
            "remaining_records": len(remaining_records),
            "both_persisted": both_persisted,
        },
    )

    return Response(
        {
            "test": "signal_transaction_commit",
            "hypothesis": "Django signals run in the same database transaction as the caller",
            "method": (
                "Create record in transaction, signal creates second record, "
                "commit transaction, check if both records are persisted"
            ),
            "results": {
                "caller_thread_id": caller_thread_id,
                "transaction_committed": True,
                "remaining_records_count": len(remaining_records),
                "remaining_records": [
                    {"id": r.id, "name": r.name, "created_in_signal": r.created_in_signal}
                    for r in remaining_records
                ],
            },
            "conclusion": {
                "same_transaction": both_persisted,
                "explanation": (
                    f"After transaction commit, {len(remaining_records)} record(s) exist. "
                    f"{'Both' if both_persisted else 'Not both'} records were persisted, "
                    f"indicating signals {'do' if both_persisted else 'do not'} "
                    f"run in the same transaction as the caller."
                ),
            },
        }
    )
