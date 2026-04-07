"""
Load ``data/toy/*.csv`` into solver input types (no Django).

Intended for integration tests and ad-hoc scripts; column names match
``scripts/generate_toy_dataset.py``.
"""

from __future__ import annotations

import csv
from pathlib import Path

from scheduler_core.types import (
    EnrollmentInput,
    PlacedSection,
    SectionPlacementInput,
    SectionSpec,
    StudentRequestSpec,
    StudentSpec,
)

def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_section_placement_input(toy_dir: Path) -> SectionPlacementInput:
    """Build :class:`SectionPlacementInput` from standard toy CSV filenames."""
    base = Path(toy_dir)
    sections_rows = _read_rows(base / "sections_to_schedule.csv")
    teachers_rows = _read_rows(base / "teachers.csv")
    rooms_rows = _read_rows(base / "rooms.csv")
    blocks_rows = _read_rows(base / "time_blocks.csv")
    ta_rows = _read_rows(base / "teacher_availability.csv")
    ra_rows = _read_rows(base / "room_availability.csv")
    sto_rows = _read_rows(base / "section_teacher_options.csv")

    sections = tuple(
        SectionSpec(
            section_id=r["section_id"].strip(),
            course_id=r["course_id"].strip(),
            min_enrollment=int(r["min_enrollment"] or 0),
            max_enrollment=int(r["max_enrollment"] or 0),
        )
        for r in sections_rows
        if r.get("section_id", "").strip()
    )
    teacher_ids = tuple(r["teacher_id"].strip() for r in teachers_rows if r.get("teacher_id", "").strip())
    room_ids = tuple(r["room_id"].strip() for r in rooms_rows if r.get("room_id", "").strip())
    block_ids = tuple(r["block_id"].strip() for r in blocks_rows if r.get("block_id", "").strip())

    teacher_availability = frozenset(
        (r["teacher_id"].strip(), r["block_id"].strip())
        for r in ta_rows
        if r.get("teacher_id", "").strip() and r.get("block_id", "").strip()
    )
    room_availability = frozenset(
        (r["room_id"].strip(), r["block_id"].strip())
        for r in ra_rows
        if r.get("room_id", "").strip() and r.get("block_id", "").strip()
    )
    section_teacher_options = frozenset(
        (r["section_id"].strip(), r["teacher_id"].strip())
        for r in sto_rows
        if r.get("section_id", "").strip() and r.get("teacher_id", "").strip()
    )

    return SectionPlacementInput(
        sections=sections,
        teacher_ids=teacher_ids,
        room_ids=room_ids,
        block_ids=block_ids,
        teacher_availability=teacher_availability,
        room_availability=room_availability,
        section_teacher_options=section_teacher_options,
    )

def load_enrollment_input(
    toy_dir: Path,
    placed_sections: tuple[PlacedSection, ...],
) -> EnrollmentInput:
    """Build :class:`EnrollmentInput` from ``students.csv`` and ``student_requests.csv``."""
    base = Path(toy_dir)
    st_rows = _read_rows(base / "students.csv")
    rq_rows = _read_rows(base / "student_requests.csv")

    students = tuple(
        StudentSpec(student_id=r["student_id"].strip())
        for r in st_rows
        if r.get("student_id", "").strip()
    )
    requests = tuple(
        StudentRequestSpec(
            student_id=r["student_id"].strip(),
            course_id=r["course_id"].strip(),
            priority=int(r["priority"] or 0),
        )
        for r in rq_rows
        if r.get("student_id", "").strip() and r.get("course_id", "").strip()
    )

    return EnrollmentInput(
        students=students,
        requests=requests,
        placed_sections=placed_sections,
    )
