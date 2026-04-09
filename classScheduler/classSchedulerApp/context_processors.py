"""Template context for nav links (teacher/student profile detection)."""

from __future__ import annotations

from .models import Student, Teacher


def scheduling_nav(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {
            "linked_teacher": None,
            "linked_student": None,
        }
    return {
        "linked_teacher": Teacher.objects.filter(user=user).first(),
        "linked_student": Student.objects.filter(user=user).first(),
    }
