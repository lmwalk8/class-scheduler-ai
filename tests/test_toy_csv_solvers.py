"""
Integration tests: toy CSVs under ``data/toy/`` to solver inputs and outputs.

Toy CSVs are **not** committed; generate them locally (``python scripts/generate_toy_dataset.py``).
If ``data/toy/`` is empty, these tests are skipped.

Ensures ``generate_toy_dataset.py`` column layouts stay compatible with
``scheduler_core.toy_csv`` and the OR-Tools solvers.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scheduler_core.section_solver import solve_section_placement
from scheduler_core.student_solver import solve_student_enrollment
from scheduler_core.toy_csv import load_enrollment_input, load_section_placement_input
from scheduler_core.types import SolveStatus, placed_sections_from_placement

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TOY_DIR = _REPO_ROOT / "data" / "toy"
_MARKER = _TOY_DIR / "sections_to_schedule.csv"

def _csvs_present() -> bool:
    return _MARKER.is_file()

@pytest.mark.skipif(not _csvs_present(), reason="CSVs missing; run scripts/generate_toy_dataset.py")
def test_toy_csv_section_placement_solves():
    problem = load_section_placement_input(_TOY_DIR)
    result = solve_section_placement(problem)
    assert result.status in (
        SolveStatus.OPTIMAL,
        SolveStatus.FEASIBLE,
    ), (
        f"Expected feasible section schedule; got {result.status!r}: {result.message}. "
        "Regenerate with a different --seed or relax constraints."
    )
    assert len(result.placements) == len(problem.sections)
    placed_ids = {p.section_id for p in result.placements}
    assert placed_ids == {s.section_id for s in problem.sections}

    used_tb = {(p.teacher_id, p.block_id) for p in result.placements}
    assert len(used_tb) == len(result.placements)

    used_rb = {(p.room_id, p.block_id) for p in result.placements}
    assert len(used_rb) == len(result.placements)

@pytest.mark.skipif(not _csvs_present(), reason="CSVs missing; run scripts/generate_toy_dataset.py")
def test_toy_csv_student_enrollment_after_section_solve():
    section_problem = load_section_placement_input(_TOY_DIR)
    sec_result = solve_section_placement(section_problem)
    assert sec_result.status in (SolveStatus.OPTIMAL, SolveStatus.FEASIBLE)

    placed = placed_sections_from_placement(
        sec_result.placements,
        section_problem.sections,
    )
    enroll_problem = load_enrollment_input(_TOY_DIR, placed)
    enroll_result = solve_student_enrollment(enroll_problem)
    assert enroll_result.status in (
        SolveStatus.OPTIMAL,
        SolveStatus.FEASIBLE,
    ), (
        f"Enrollment unexpectedly unsolved: {enroll_result.status!r} {enroll_result.message}"
    )

    for e in enroll_result.enrollments:
        assert e.student_id in {s.student_id for s in enroll_problem.students}
