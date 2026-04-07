"""
Unit tests for the student enrollment solver.

Run from repo root, e.g.:

pytest tests/test_student_solver.py

Coverage: happy path, empty inputs, infeasible / invalid cases, capacity,
time-block conflicts, and choice among parallel sections.
"""

from scheduler_core.student_solver import solve_student_enrollment
from scheduler_core.types import (
    EnrollmentAssignment,
    EnrollmentInput,
    PlacedSection,
    SolveStatus,
    StudentRequestSpec,
    StudentSpec,
)

def test_solve_student_enrollment_assigns_matching_section():
    placed = (
        PlacedSection(
            section_id="CS101-A",
            course_id="CS101",
            block_id="B1",
            max_enrollment=30,
        ),
    )
    problem = EnrollmentInput(
        students=(StudentSpec(student_id="1"),),
        requests=(StudentRequestSpec(student_id="1", course_id="CS101", priority=1),),
        placed_sections=placed,
    )
    result = solve_student_enrollment(problem)
    assert result.status in (SolveStatus.OPTIMAL, SolveStatus.FEASIBLE)
    assert result.enrollments == (
        EnrollmentAssignment(student_id="1", section_id="CS101-A"),
    )

def test_solve_student_enrollment_two_students_distinct_sections():
    placed = (
        PlacedSection("CS101-A", "CS101", "B1", 30),
        PlacedSection("CS102-A", "CS102", "B2", 30),
    )
    problem = EnrollmentInput(
        students=(StudentSpec("1"), StudentSpec("2")),
        requests=(
            StudentRequestSpec("1", "CS101", priority=1),
            StudentRequestSpec("2", "CS102", priority=1),
        ),
        placed_sections=placed,
    )
    result = solve_student_enrollment(problem)
    assert result.status in (SolveStatus.OPTIMAL, SolveStatus.FEASIBLE)
    assert len(result.enrollments) == 2
    by_student = {e.student_id: e.section_id for e in result.enrollments}
    assert by_student["1"] == "CS101-A"
    assert by_student["2"] == "CS102-A"

def test_solve_student_enrollment_parallel_sections_one_choice():
    """At most one section per (student, course) when multiple offerings exist."""
    placed = (
        PlacedSection("CS101-A", "CS101", "B1", 30),
        PlacedSection("CS101-B", "CS101", "B2", 30),
    )
    problem = EnrollmentInput(
        students=(StudentSpec("1"),),
        requests=(StudentRequestSpec("1", "CS101", priority=1),),
        placed_sections=placed,
    )
    result = solve_student_enrollment(problem)
    assert result.status in (SolveStatus.OPTIMAL, SolveStatus.FEASIBLE)
    assert len(result.enrollments) == 1
    assert result.enrollments[0].student_id == "1"
    assert result.enrollments[0].section_id in ("CS101-A", "CS101-B")

def test_solve_student_enrollment_respects_capacity():
    """Only one seat; solver assigns at most one student to that section."""
    placed = (PlacedSection("CS101-A", "CS101", "B1", max_enrollment=1),)
    problem = EnrollmentInput(
        students=(StudentSpec("1"), StudentSpec("2")),
        requests=(
            StudentRequestSpec("1", "CS101", priority=1),
            StudentRequestSpec("2", "CS101", priority=1),
        ),
        placed_sections=placed,
    )
    result = solve_student_enrollment(problem)
    assert result.status in (SolveStatus.OPTIMAL, SolveStatus.FEASIBLE)
    assert len(result.enrollments) == 1
    assert result.enrollments[0].section_id == "CS101-A"

def test_solve_student_enrollment_same_block_conflict_prefers_higher_priority():
    """One section per time block per student; higher-priority request wins."""
    placed = (
        PlacedSection("CS101-A", "CS101", "B1", 30),
        PlacedSection("CS102-A", "CS102", "B1", 30),
    )
    problem = EnrollmentInput(
        students=(StudentSpec("1"),),
        requests=(
            StudentRequestSpec("1", "CS101", priority=1),
            StudentRequestSpec("1", "CS102", priority=2),
        ),
        placed_sections=placed,
    )
    result = solve_student_enrollment(problem)
    assert result.status in (SolveStatus.OPTIMAL, SolveStatus.FEASIBLE)
    assert result.enrollments == (
        EnrollmentAssignment(student_id="1", section_id="CS101-A"),
    )

def test_solve_student_enrollment_invalid_unknown_student_on_request():
    problem = EnrollmentInput(
        students=(StudentSpec("1"),),
        requests=(StudentRequestSpec(student_id="99", course_id="CS101", priority=1),),
        placed_sections=(PlacedSection("CS101-A", "CS101", "B1", 30),),
    )
    result = solve_student_enrollment(problem)
    assert result.status == SolveStatus.INVALID
    assert "99" in result.message
    assert result.enrollments == ()

def test_solve_student_enrollment_infeasible_course_mismatch():
    placed = (PlacedSection("CS101-A", "CS101", "B1", 30),)
    problem = EnrollmentInput(
        students=(StudentSpec("1"),),
        requests=(StudentRequestSpec("1", "CS999", priority=1),),
        placed_sections=placed,
    )
    result = solve_student_enrollment(problem)
    assert result.status == SolveStatus.INFEASIBLE
    assert result.enrollments == ()

def test_solve_student_enrollment_no_requests():
    problem = EnrollmentInput(
        students=(StudentSpec(student_id="1"),),
        requests=(),
        placed_sections=(),
    )
    result = solve_student_enrollment(problem)
    assert result.status == SolveStatus.FEASIBLE
    assert result.enrollments == ()

def test_solve_student_enrollment_no_students():
    problem = EnrollmentInput(
        students=(),
        requests=(StudentRequestSpec(student_id="1", course_id="CS101", priority=1),),
        placed_sections=(),
    )
    result = solve_student_enrollment(problem)
    assert result.status == SolveStatus.FEASIBLE
    assert result.enrollments == ()

def test_solve_student_enrollment_no_sections_but_requests():
    problem = EnrollmentInput(
        students=(StudentSpec(student_id="1"),),
        requests=(StudentRequestSpec(student_id="1", course_id="CS101", priority=1),),
        placed_sections=(),
    )
    result = solve_student_enrollment(problem)
    assert result.status == SolveStatus.INFEASIBLE
    assert result.enrollments == ()
