"""
Example pipeline: section placement → student enrollment (no Django).

Run from repo root, e.g.:

python scripts/student_course_enrollment_solver.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Repo root on sys.path when run as `python scripts/...` from repo root
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scheduler_core.section_solver import solve_section_placement
from scheduler_core.student_solver import solve_student_enrollment
from scheduler_core.types import (
    EnrollmentInput,
    SectionPlacementInput,
    SectionSpec,
    StudentRequestSpec,
    StudentSpec,
    placed_sections_from_placement,
)

def main() -> None:
    # Minimal demo instance (replace with CSV → dataclass loading later)
    sections = (
        SectionSpec("SEC-A", "CS101", 0, 30),
        SectionSpec("SEC-B", "CS101", 0, 30),
    )
    problem = SectionPlacementInput(
        sections=sections,
        teacher_ids=("T1", "T2"),
        room_ids=("R1", "R2"),
        block_ids=("B1", "B2"),
        teacher_availability=frozenset(
            {("T1", "B1"), ("T1", "B2"), ("T2", "B1"), ("T2", "B2")}
        ),
        room_availability=frozenset(
            {("R1", "B1"), ("R1", "B2"), ("R2", "B1"), ("R2", "B2")}
        ),
        section_teacher_options=frozenset(
            {("SEC-A", "T1"), ("SEC-B", "T2")}
        ),
    )
    sec_result = solve_section_placement(problem)
    print("Section solve:", sec_result.status, sec_result.message)
    if not sec_result.placements:
        return

    placed = placed_sections_from_placement(sec_result.placements, sections)
    students = (StudentSpec("S1"), StudentSpec("S2"))
    requests = (
        StudentRequestSpec("S1", "CS101", priority=1),
        StudentRequestSpec("S2", "CS101", priority=1),
    )
    enroll = solve_student_enrollment(
        EnrollmentInput(
            students=students,
            requests=requests,
            placed_sections=placed,
        )
    )
    print("Enrollment solve:", enroll.status, enroll.message)
    for e in enroll.enrollments:
        print(f"  {e.student_id} -> {e.section_id}")

if __name__ == "__main__":
    main()
