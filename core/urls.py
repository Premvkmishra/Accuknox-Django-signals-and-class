"""
URL configuration for the core application.

This module defines URL patterns for API endpoints related to
signal investigation and rectangle testing.
"""
from django.urls import path

from core import views

app_name: str = "core"

urlpatterns: list = [
    path("signal/sync/", views.signal_sync_test, name="signal_sync_test"),
    path("signal/thread/", views.signal_thread_test, name="signal_thread_test"),
    path("signal/transaction/", views.signal_transaction_test, name="signal_transaction_test"),
    path(
        "signal/transaction/commit/",
        views.signal_transaction_commit_test,
        name="signal_transaction_commit_test",
    ),
]
