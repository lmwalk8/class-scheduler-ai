"""Django-free scheduling solvers (OR-Tools CP-SAT)."""

from scheduler_core.types import (
    EnrollmentAssignment,
    EnrollmentInput,
    EnrollmentResult,
    PlacedSection,
    SectionPlacement,
    SectionPlacementInput,
    SectionPlacementResult,
    SectionSpec,
    SolveStatus,
    StudentRequestSpec,
    StudentSpec,
    placed_sections_from_placement,
)

__all__ = [
    "EnrollmentAssignment",
    "EnrollmentInput",
    "EnrollmentResult",
    "PlacedSection",
    "SectionPlacement",
    "SectionPlacementInput",
    "SectionPlacementResult",
    "SectionSpec",
    "SolveStatus",
    "StudentRequestSpec",
    "StudentSpec",
    "placed_sections_from_placement",
    "solve_section_placement",
    "solve_student_enrollment",
]

def __getattr__(name: str):
    if name == "solve_section_placement":
        from scheduler_core.section_solver import solve_section_placement

        return solve_section_placement
    if name == "solve_student_enrollment":
        from scheduler_core.student_solver import solve_student_enrollment

        return solve_student_enrollment
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
