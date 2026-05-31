"""
Database models for the core application.

This module defines Django models used for signal investigation and testing.
"""
import logging
import threading
import time
from typing import Any

from django.db import models, transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class SignalTestModel(models.Model):
    """Model used for testing Django signal behavior.

    This model is used to investigate signal synchronization, threading,
    and transaction behavior in Django.
    """

    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Fields for signal investigation
    caller_thread_id = models.CharField(max_length=255, null=True, blank=True)
    signal_thread_id = models.CharField(max_length=255, null=True, blank=True)
    signal_executed = models.BooleanField(default=False)
    signal_delay_seconds = models.FloatField(default=0.0)
    signal_execution_time = models.FloatField(null=True, blank=True)

    class Meta:
        """Meta configuration for SignalTestModel."""

        verbose_name = "Signal Test Model"
        verbose_name_plural = "Signal Test Models"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return string representation of the model."""
        return f"SignalTestModel(id={self.id}, name={self.name})"


class TransactionTestModel(models.Model):
    """Model used for testing signal transaction behavior.

    This model is used to investigate whether signals run in the same
    database transaction as the caller.
    """

    name = models.CharField(max_length=255)
    created_in_signal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta configuration for TransactionTestModel."""

        verbose_name = "Transaction Test Model"
        verbose_name_plural = "Transaction Test Models"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return string representation of the model."""
        return f"TransactionTestModel(id={self.id}, name={self.name})"


class SignalExecutionLog(models.Model):
    """Model to log signal execution details for analysis.

    This model stores detailed information about signal execution,
    including timing, thread information, and transaction context.
    """

    signal_name = models.CharField(max_length=255)
    caller_thread_id = models.CharField(max_length=255)
    signal_thread_id = models.CharField(max_length=255)
    same_thread = models.BooleanField(default=False)
    execution_time_ms = models.FloatField(null=True, blank=True)
    delay_seconds = models.FloatField(default=0.0)
    in_transaction = models.BooleanField(default=False)
    transaction_successful = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta configuration for SignalExecutionLog."""

        verbose_name = "Signal Execution Log"
        verbose_name_plural = "Signal Execution Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["signal_name"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the model."""
        return (
            f"SignalExecutionLog(signal={self.signal_name}, "
            f"same_thread={self.same_thread})"
        )
