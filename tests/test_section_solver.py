"""
Unit tests for the section placement solver.

Run from repo root, e.g.:

pytest tests/test_section_solver.py

Coverage: single/multiple sections, INVALID (duplicates, missing options),
INFEASIBLE (no resources, teacher/room grid exhaustion), and optional
teacher_ids list (unused by solver).
"""

from scheduler_core.section_solver import solve_section_placement
from scheduler_core.types import (
    SectionPlacementInput,
    SectionSpec,
    SolveStatus,
)

# Shared fixtures for a small feasible grid
_TEACHER_AVAIL = frozenset(
    {("T1", "B1"), ("T1", "B2"), ("T2", "B1"), ("T2", "B2")}
)
_ROOM_AVAIL = frozenset(
    {("R1", "B1"), ("R1", "B2"), ("R2", "B1"), ("R2", "B2")}
)
_OPTS_CS101A = frozenset({("CS101-A", "T1"), ("CS101-A", "T2")})

_CS101A = SectionSpec(
    section_id="CS101-A",
    course_id="CS101",
    min_enrollment=0,
    max_enrollment=30,
)

def _full_problem(
    *,
    sections: tuple[SectionSpec, ...] = (_CS101A,),
    teacher_ids: tuple[str, ...] = ("T1", "T2"),
    room_ids: tuple[str, ...] = ("R1", "R2"),
    block_ids: tuple[str, ...] = ("B1", "B2"),
    teacher_availability: frozenset[tuple[str, str]] = _TEACHER_AVAIL,
    room_availability: frozenset[tuple[str, str]] = _ROOM_AVAIL,
    section_teacher_options: frozenset[tuple[str, str]] = _OPTS_CS101A,
) -> SectionPlacementInput:
    return SectionPlacementInput(
        sections=sections,
        teacher_ids=teacher_ids,
        room_ids=room_ids,
        block_ids=block_ids,
        teacher_availability=teacher_availability,
        room_availability=room_availability,
        section_teacher_options=section_teacher_options,
    )

def test_solve_section_placement_assigns_matching_section():
    problem = _full_problem()
    result = solve_section_placement(problem)
    assert result.status in (SolveStatus.OPTIMAL, SolveStatus.FEASIBLE)
    assert len(result.placements) == 1
    p = result.placements[0]
    assert p.section_id == "CS101-A"
    assert p.teacher_id in ("T1", "T2")
    assert p.room_id in ("R1", "R2")
    assert p.block_id in ("B1", "B2")
    assert (p.teacher_id, p.block_id) in problem.teacher_availability
    assert (p.room_id, p.block_id) in problem.room_availability
    assert (p.section_id, p.teacher_id) in problem.section_teacher_options

def test_solve_section_placement_no_sections():
    problem = _full_problem(sections=())
    result = solve_section_placement(problem)
    assert result.status == SolveStatus.FEASIBLE
    assert result.placements == ()
    assert "No sections" in result.message

def test_solve_section_placement_duplicate_section_id_invalid():
    dup = (
        SectionSpec("CS101-A", "CS101", 0, 30),
        SectionSpec("CS101-A", "CS101", 0, 30),
    )
    problem = _full_problem(
        sections=dup,
        section_teacher_options=frozenset(
            {("CS101-A", "T1"), ("CS101-A", "T2")}
        ),
    )
    result = solve_section_placement(problem)
    assert result.status == SolveStatus.INVALID
    assert "Duplicate section_id" in result.message
    assert result.placements == ()

def test_solve_section_placement_multi_section_disjoint_teachers():
    """Two sections with disjoint teacher options should both schedule without conflicts."""
    cs201a = SectionSpec("CS201-A", "CS201", 0, 30)
    opts = frozenset({("CS101-A", "T1"), ("CS201-A", "T2")})
    problem = _full_problem(sections=(_CS101A, cs201a), section_teacher_options=opts)
    result = solve_section_placement(problem)
    assert result.status in (SolveStatus.OPTIMAL, SolveStatus.FEASIBLE)
    assert len(result.placements) == 2
    by_section = {p.section_id: p for p in result.placements}
    assert set(by_section) == {"CS101-A", "CS201-A"}
    assert by_section["CS101-A"].teacher_id == "T1"
    assert by_section["CS201-A"].teacher_id == "T2"
    used_tb = {(p.teacher_id, p.block_id) for p in result.placements}
    assert len(used_tb) == 2
    used_rb = {(p.room_id, p.block_id) for p in result.placements}
    assert len(used_rb) == 2
    for p in result.placements:
        assert (p.teacher_id, p.block_id) in problem.teacher_availability
        assert (p.room_id, p.block_id) in problem.room_availability

def test_solve_section_placement_second_section_missing_options_invalid():
    cs201a = SectionSpec("CS201-A", "CS201", 0, 30)
    problem = _full_problem(
        sections=(_CS101A, cs201a),
        section_teacher_options=_OPTS_CS101A,
    )
    result = solve_section_placement(problem)
    assert result.status == SolveStatus.INVALID
    assert "CS201-A" in result.message
    assert "section_teacher_options" in result.message

def test_solve_section_placement_no_section_teacher_options_invalid():
    """Section listed but no eligible teachers → INVALID before search."""
    problem = _full_problem(section_teacher_options=frozenset())
    result = solve_section_placement(problem)
    assert result.status == SolveStatus.INVALID
    assert result.placements == ()

def test_solve_section_placement_teacher_in_options_but_never_available_infeasible():
    """Options name a teacher with no (teacher, block) in availability → no triples."""
    problem = _full_problem(
        section_teacher_options=frozenset({("CS101-A", "T3")}),
        teacher_availability=_TEACHER_AVAIL,
    )
    result = solve_section_placement(problem)
    assert result.status == SolveStatus.INFEASIBLE
    assert "CS101-A" in result.message
    assert result.placements == ()

def test_solve_section_placement_two_sections_one_teacher_slot_infeasible():
    """Both sections only share T1 at one block/room; at most one assignment."""
    cs101b = SectionSpec("CS101-B", "CS101", 0, 30)
    avail_t1_b1 = frozenset({("T1", "B1")})
    room_r1_b1 = frozenset({("R1", "B1")})
    opts_both_t1 = frozenset({("CS101-A", "T1"), ("CS101-B", "T1")})
    problem = _full_problem(
        sections=(_CS101A, cs101b),
        room_ids=("R1",),
        block_ids=("B1",),
        teacher_availability=avail_t1_b1,
        room_availability=room_r1_b1,
        section_teacher_options=opts_both_t1,
    )
    result = solve_section_placement(problem)
    assert result.status == SolveStatus.INFEASIBLE
    assert result.placements == ()

def test_solve_section_placement_no_rooms_infeasible():
    """No rooms → no feasible (teacher, room, block) triples."""
    problem = _full_problem(room_ids=())
    result = solve_section_placement(problem)
    assert result.status == SolveStatus.INFEASIBLE
    assert result.placements == ()

def test_solve_section_placement_no_block_ids_infeasible():
    problem = _full_problem(block_ids=())
    result = solve_section_placement(problem)
    assert result.status == SolveStatus.INFEASIBLE
    assert result.placements == ()

def test_solve_section_placement_no_teacher_availability_infeasible():
    problem = _full_problem(teacher_availability=frozenset())
    result = solve_section_placement(problem)
    assert result.status == SolveStatus.INFEASIBLE
    assert result.placements == ()

def test_solve_section_placement_no_room_availability_infeasible():
    problem = _full_problem(room_availability=frozenset())
    result = solve_section_placement(problem)
    assert result.status == SolveStatus.INFEASIBLE
    assert result.placements == ()

def test_solve_section_placement_teacher_ids_unused_but_options_valid_still_solves():
    """Solver keys off section_teacher_options, not teacher_ids; still finds a schedule."""
    problem = _full_problem(teacher_ids=())
    result = solve_section_placement(problem)
    assert result.status in (SolveStatus.OPTIMAL, SolveStatus.FEASIBLE)
    assert len(result.placements) == 1
    assert result.placements[0].section_id == "CS101-A"

def test_solve_section_placement_single_room_still_feasible():
    """Only R1 listed: one section still gets a valid (T, R1, B) triple."""
    problem = _full_problem(room_ids=("R1",))
    result = solve_section_placement(problem)
    assert result.status in (SolveStatus.OPTIMAL, SolveStatus.FEASIBLE)
    assert len(result.placements) == 1
    assert result.placements[0].room_id == "R1"
