"""
Plain dataclasses for scheduling inputs and outputs.

Keep these Django-free so solvers stay testable with CSVs or fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SolveStatus(str, Enum):
    """High-level outcome after calling a solver."""

    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    UNKNOWN = "UNKNOWN"
    INVALID = "INVALID"


@dataclass(frozen=True)
class SectionSpec:
    """One section row to place (time / room / teacher)."""

    section_id: str
    course_id: str
    min_enrollment: int = 0
    max_enrollment: int = 999


@dataclass(frozen=True)
class PlacedSection:
    """Section after phase-1 placement; feeds the student enrollment solver."""

    section_id: str
    course_id: str
    block_id: str
    max_enrollment: int


@dataclass(frozen=True)
class SectionPlacementInput:
    sections: tuple[SectionSpec, ...]
    teacher_ids: tuple[str, ...]
    room_ids: tuple[str, ...]
    block_ids: tuple[str, ...]
    teacher_availability: frozenset[tuple[str, str]]  # (teacher_id, block_id)
    room_availability: frozenset[tuple[str, str]]  # (room_id, block_id)
    section_teacher_options: frozenset[tuple[str, str]]  # (section_id, teacher_id)


@dataclass(frozen=True)
class SectionPlacement:
    section_id: str
    teacher_id: str
    room_id: str
    block_id: str


@dataclass(frozen=True)
class SectionPlacementResult:
    status: SolveStatus
    placements: tuple[SectionPlacement, ...] = ()
    objective_value: Optional[int] = None
    solver_wall_time_seconds: Optional[float] = None
    message: str = ""


@dataclass(frozen=True)
class StudentSpec:
    student_id: str


@dataclass(frozen=True)
class StudentRequestSpec:
    student_id: str
    course_id: str
    priority: int  # lower number = higher preference (matches toy CSV)


@dataclass(frozen=True)
class EnrollmentInput:
    students: tuple[StudentSpec, ...]
    requests: tuple[StudentRequestSpec, ...]
    placed_sections: tuple[PlacedSection, ...]


@dataclass(frozen=True)
class EnrollmentAssignment:
    student_id: str
    section_id: str


@dataclass(frozen=True)
class EnrollmentResult:
    status: SolveStatus
    enrollments: tuple[EnrollmentAssignment, ...] = ()
    objective_value: Optional[int] = None
    solver_wall_time_seconds: Optional[float] = None
    message: str = ""


def placed_sections_from_placement(
    placements: tuple[SectionPlacement, ...],
    section_specs: tuple[SectionSpec, ...],
) -> tuple[PlacedSection, ...]:
    """Build ``PlacedSection`` rows for the student solver from section placement output."""
    by_id = {s.section_id: s for s in section_specs}
    out: list[PlacedSection] = []
    for p in placements:
        spec = by_id.get(p.section_id)
        if spec is None:
            raise ValueError(f"Unknown section_id in placement: {p.section_id!r}")
        out.append(
            PlacedSection(
                section_id=p.section_id,
                course_id=spec.course_id,
                block_id=p.block_id,
                max_enrollment=spec.max_enrollment,
            )
        )
    return tuple(out)
