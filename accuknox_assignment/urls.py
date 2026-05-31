"""
URL configuration for accuknox_assignment project.

This module defines the URL patterns for the Django project,
including routes for API endpoints and admin interface.
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns: list = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
]
