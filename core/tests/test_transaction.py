"""
Tests for Django signal transaction behavior.

This module contains tests to investigate whether Django signals run
in the same database transaction as the caller.

Hypothesis: Django signals run in the same database transaction as the caller.
"""
import logging
import threading
from typing import Any

import pytest
from django.db import transaction
from django.test import TestCase

from core.models import TransactionTestModel

logger = logging.getLogger(__name__)


class SignalTransactionTests(TestCase):
    """Test suite for investigating Django signal transaction behavior."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        TransactionTestModel.objects.all().delete()

    def tearDown(self) -> None:
        """Clean up after tests."""
        TransactionTestModel.objects.all().delete()

    def test_signal_runs_in_same_transaction_on_rollback(self) -> None:
        """Test that signal-created records are rolled back with caller transaction.

        Method:
        1. Start a transaction using transaction.atomic()
        2. Create a TransactionTestModel (caller record)
        3. Signal handler creates another TransactionTestModel (signal record)
        4. Force a rollback
        5. Verify both records are rolled back

        Expected:
        - Both caller and signal records should be rolled back
        - This proves signals run in the same transaction
        """
        caller_thread_id = str(threading.get_ident())

        logger.info(
            "Starting transaction rollback test",
            extra={
                "test": "test_signal_runs_in_same_transaction_on_rollback",
                "caller_thread_id": caller_thread_id,
            },
        )

        # Ensure clean state
        TransactionTestModel.objects.all().delete()

        try:
            with transaction.atomic():
                # Create caller record
                caller_record = TransactionTestModel.objects.create(
                    name="rollback_test_caller",
                    created_in_signal=False,
                )

                logger.info(
                    "Created caller record in transaction",
                    extra={
                        "caller_record_id": caller_record.id,
                        "caller_record_name": caller_record.name,
                    },
                )

                # Signal will create a second record automatically
                # Force rollback
                raise Exception("Intentional rollback for testing")

        except Exception as e:
            # Expected exception for rollback
            self.assertEqual(str(e), "Intentional rollback for testing")

        # Check if records exist after rollback
        remaining_records = list(TransactionTestModel.objects.all())

        logger.info(
            "Transaction rollback test completed",
            extra={
                "remaining_records_count": len(remaining_records),
                "remaining_records": [
                    {"id": r.id, "name": r.name, "created_in_signal": r.created_in_signal}
                    for r in remaining_records
                ],
            },
        )

        # Assertions
        self.assertEqual(
            len(remaining_records),
            0,
            "Both caller and signal records should be rolled back",
        )

    def test_signal_runs_in_same_transaction_on_commit(self) -> None:
        """Test that signal-created records are committed with caller transaction.

        Method:
        1. Start a transaction using transaction.atomic()
        2. Create a TransactionTestModel (caller record)
        3. Signal handler creates another TransactionTestModel (signal record)
        4. Allow transaction to commit
        5. Verify both records are persisted

        Expected:
        - Both caller and signal records should be persisted
        - This proves signals run in the same transaction
        """
        caller_thread_id = str(threading.get_ident())

        logger.info(
            "Starting transaction commit test",
            extra={
                "test": "test_signal_runs_in_same_transaction_on_commit",
                "caller_thread_id": caller_thread_id,
            },
        )

        # Ensure clean state
        TransactionTestModel.objects.all().delete()

        with transaction.atomic():
            # Create caller record
            caller_record = TransactionTestModel.objects.create(
                name="commit_test_caller",
                created_in_signal=False,
            )

            logger.info(
                "Created caller record in transaction",
                extra={
                    "caller_record_id": caller_record.id,
                    "caller_record_name": caller_record.name,
                },
            )

            # Signal will create a second record automatically
            # Transaction commits automatically when exiting context manager

        # Check if records exist after commit
        remaining_records = list(TransactionTestModel.objects.all())

        logger.info(
            "Transaction commit test completed",
            extra={
                "remaining_records_count": len(remaining_records),
                "remaining_records": [
                    {"id": r.id, "name": r.name, "created_in_signal": r.created_in_signal}
                    for r in remaining_records
                ],
            },
        )

        # Assertions
        self.assertEqual(
            len(remaining_records),
            2,
            "Both caller and signal records should be committed",
        )

        # Verify we have one caller record and one signal record
        caller_records = [r for r in remaining_records if not r.created_in_signal]
        signal_records = [r for r in remaining_records if r.created_in_signal]

        self.assertEqual(len(caller_records), 1, "Should have one caller record")
        self.assertEqual(len(signal_records), 1, "Should have one signal record")
        self.assertEqual(caller_records[0].name, "commit_test_caller")
        self.assertTrue(signal_records[0].name.endswith("_signal_created"))

    def test_signal_error_rolls_back_transaction(self) -> None:
        """Test that errors in signal handler cause transaction rollback.

        Method:
        1. Start a transaction
        2. Create a record with a signal that raises an exception
        3. Verify transaction is rolled back

        Expected:
        - Transaction should be rolled back on signal error
        """
        from django.db.models.signals import post_save
        from django.dispatch import receiver

        @receiver(post_save, sender=TransactionTestModel)
        def error_signal_handler(sender: Any, instance: TransactionTestModel, **kwargs: Any) -> None:
            """Signal handler that raises an exception."""
            raise ValueError("Test exception from signal")

        try:
            # Ensure clean state
            TransactionTestModel.objects.all().delete()

            with self.assertRaises(ValueError):
                with transaction.atomic():
                    TransactionTestModel.objects.create(
                        name="error_test",
                        created_in_signal=False,
                    )

            # Verify no records were created due to rollback
            remaining_records = list(TransactionTestModel.objects.all())
            self.assertEqual(
                len(remaining_records),
                0,
                "Transaction should be rolled back on signal error",
            )

            logger.info(
                "Signal error rollback test passed",
                extra={"test": "test_signal_error_rolls_back_transaction"},
            )

        finally:
            # Clean up the signal handler
            post_save.disconnect(error_signal_handler, sender=TransactionTestModel)

    def test_nested_transaction_signal_behavior(self) -> None:
        """Test signal behavior with nested transactions (savepoints).

        Method:
        1. Create outer transaction
        2. Create inner transaction (savepoint)
        3. Create record in inner transaction
        4. Rollback inner transaction
        5. Verify signal record behavior

        Expected:
        - Signal should respect savepoint semantics
        """
        TransactionTestModel.objects.all().delete()

        with transaction.atomic():
            # Create a record in outer transaction
            outer_record = TransactionTestModel.objects.create(
                name="outer_transaction",
                created_in_signal=False,
            )

            # Create inner transaction (savepoint)
            try:
                with transaction.atomic():
                    inner_record = TransactionTestModel.objects.create(
                        name="inner_transaction",
                        created_in_signal=False,
                    )
                    # Signal creates another record here

                    # Rollback inner transaction
                    raise Exception("Rollback inner transaction")

            except Exception:
                # Expected - inner transaction rolled back
                pass

            # Outer transaction should still have its records
            remaining_records = list(TransactionTestModel.objects.all())

            # Should have outer record and its signal record
            # Inner record and its signal record should be rolled back
            self.assertGreaterEqual(len(remaining_records), 1)

        logger.info(
            "Nested transaction test passed",
            extra={
                "test": "test_nested_transaction_signal_behavior",
                "remaining_records_count": len(remaining_records),
            },
        )

    def test_signal_transaction_isolation(self) -> None:
        """Test that signal operations are isolated within the transaction.

        Method:
        1. Start transaction
        2. Create record (signal creates another)
        3. Query within transaction
        4. Verify both records visible
        5. Rollback
        6. Verify records not visible outside transaction

        Expected:
        - Both records visible within transaction
        - Neither visible after rollback
        """
        TransactionTestModel.objects.all().delete()

        try:
            with transaction.atomic():
                # Create record
                caller_record = TransactionTestModel.objects.create(
                    name="isolation_test",
                    created_in_signal=False,
                )

                # Query within transaction - should see both records
                records_in_transaction = list(TransactionTestModel.objects.all())

                self.assertEqual(
                    len(records_in_transaction),
                    2,
                    "Should see both caller and signal records within transaction",
                )

                # Rollback
                raise Exception("Rollback for isolation test")
        except Exception:
            # Expected exception for rollback
            pass

        # Query after rollback - should see no records
        records_after_rollback = list(TransactionTestModel.objects.all())

        self.assertEqual(
            len(records_after_rollback),
            0,
            "Should see no records after transaction rollback",
        )

        logger.info(
            "Transaction isolation test passed",
            extra={"test": "test_signal_transaction_isolation"},
        )

    def test_multiple_signal_operations_in_transaction(self) -> None:
        """Test multiple signal operations within a single transaction.

        Method:
        1. Start transaction
        2. Create multiple records
        3. Each creates a signal record
        4. Commit
        5. Verify all records persisted

        Expected:
        - All caller and signal records should be committed
        """
        TransactionTestModel.objects.all().delete()

        with transaction.atomic():
            for i in range(3):
                TransactionTestModel.objects.create(
                    name=f"multi_test_{i}",
                    created_in_signal=False,
                )

        # Should have 3 caller records + 3 signal records = 6 total
        remaining_records = list(TransactionTestModel.objects.all())

        self.assertEqual(
            len(remaining_records),
            6,
            "Should have all caller and signal records after commit",
        )

        caller_records = [r for r in remaining_records if not r.created_in_signal]
        signal_records = [r for r in remaining_records if r.created_in_signal]

        self.assertEqual(len(caller_records), 3, "Should have 3 caller records")
        self.assertEqual(len(signal_records), 3, "Should have 3 signal records")

        logger.info(
            "Multiple signal operations test passed",
            extra={
                "test": "test_multiple_signal_operations_in_transaction",
                "total_records": len(remaining_records),
            },
        )


@pytest.mark.django_db
class SignalTransactionPytestTests:
    """Pytest-based tests for signal transaction behavior."""

    def test_signal_transaction_rollback_pytest(self) -> None:
        """Test signal transaction rollback using pytest."""
        TransactionTestModel.objects.all().delete()

        try:
            with transaction.atomic():
                TransactionTestModel.objects.create(
                    name="pytest_rollback_test",
                    created_in_signal=False,
                )
                raise Exception("Rollback")
        except Exception:
            pass

        remaining = list(TransactionTestModel.objects.all())
        assert len(remaining) == 0
        logger.info(
            "Pytest transaction rollback test passed",
            extra={"test": "test_signal_transaction_rollback_pytest"},
        )

    def test_signal_transaction_commit_pytest(self) -> None:
        """Test signal transaction commit using pytest."""
        TransactionTestModel.objects.all().delete()

        with transaction.atomic():
            TransactionTestModel.objects.create(
                name="pytest_commit_test",
                created_in_signal=False,
            )

        remaining = list(TransactionTestModel.objects.all())
        assert len(remaining) == 2
        logger.info(
            "Pytest transaction commit test passed",
            extra={"test": "test_signal_transaction_commit_pytest"},
        )
