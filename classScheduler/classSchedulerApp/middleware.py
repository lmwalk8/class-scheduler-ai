"""
Per-request timezone activation.

Django 6 no longer ships ``django.middleware.timezone.TimeZoneMiddleware``; the docs
show a custom pattern. This activates ``settings.TIME_ZONE`` (from ``DJANGO_TIME_ZONE``)
so template filters like ``localtime`` match the local timezone.
"""

from __future__ import annotations

import zoneinfo

from django.conf import settings
from django.utils import timezone

class ActivateSettingsTimezoneMiddleware:
    """Activate ``settings.TIME_ZONE`` for this request, then deactivate after."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, "USE_TZ", False):
            try:
                timezone.activate(zoneinfo.ZoneInfo(settings.TIME_ZONE))
            except zoneinfo.ZoneInfoNotFoundError:
                timezone.deactivate()
        try:
            return self.get_response(request)
        finally:
            if getattr(settings, "USE_TZ", False):
                timezone.deactivate()
