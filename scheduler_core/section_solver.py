"""
Section scheduling with OR-Tools CP-SAT.

Each section is assigned exactly one (teacher, room, time block) from feasible
combinations: section–teacher options, teacher availability, room availability.
"""

from __future__ import annotations

import time
from typing import List

from ortools.sat.python import cp_model

from scheduler_core.types import (
    SectionPlacement,
    SectionPlacementInput,
    SectionPlacementResult,
    SolveStatus,
)

def _cp_status_to_solve_status(status: int) -> SolveStatus:
    if status == cp_model.OPTIMAL:
        return SolveStatus.OPTIMAL
    if status == cp_model.FEASIBLE:
        return SolveStatus.FEASIBLE
    if status == cp_model.INFEASIBLE:
        return SolveStatus.INFEASIBLE
    return SolveStatus.UNKNOWN

def _build_feasible_triples(problem: SectionPlacementInput) -> List[tuple[str, str, str, str]]:
    """List of (section_id, teacher_id, room_id, block_id)."""
    options_by_section: dict[str, set[str]] = {}
    for sid, tid in problem.section_teacher_options:
        options_by_section.setdefault(sid, set()).add(tid)

    triples: List[tuple[str, str, str, str]] = []
    for sec in problem.sections:
        teachers = options_by_section.get(sec.section_id, set())
        if not teachers:
            continue
        for t in teachers:
            for r in problem.room_ids:
                for b in problem.block_ids:
                    if (t, b) not in problem.teacher_availability:
                        continue
                    if (r, b) not in problem.room_availability:
                        continue
                    triples.append((sec.section_id, t, r, b))
    return triples

def solve_section_placement(
    problem: SectionPlacementInput,
    *,
    time_limit_seconds: float | None = 30.0,
) -> SectionPlacementResult:
    """
    Assign every section in ``problem.sections`` to one teacher, room, and block.

    Returns INFEASIBLE if no complete assignment exists, or INVALID if input
    is inconsistent (e.g. section with no allowed teachers).
    """
    if not problem.sections:
        return SectionPlacementResult(
            status=SolveStatus.FEASIBLE,
            placements=(),
            message="No sections to schedule.",
        )

    section_ids = [s.section_id for s in problem.sections]
    if len(set(section_ids)) != len(section_ids):
        return SectionPlacementResult(
            status=SolveStatus.INVALID,
            message="Duplicate section_id in sections.",
        )

    options_by_section: dict[str, set[str]] = {}
    for sid, tid in problem.section_teacher_options:
        options_by_section.setdefault(sid, set()).add(tid)

    for sec in problem.sections:
        if sec.section_id not in options_by_section:
            return SectionPlacementResult(
                status=SolveStatus.INVALID,
                message=f"Section {sec.section_id!r} has no section_teacher_options.",
            )

    feasible = _build_feasible_triples(problem)
    # Group feasible indices by section
    by_section: dict[str, List[int]] = {sid: [] for sid in section_ids}
    for i, (sid, _t, _r, _b) in enumerate(feasible):
        by_section[sid].append(i)

    for sid in section_ids:
        if not by_section[sid]:
            return SectionPlacementResult(
                status=SolveStatus.INFEASIBLE,
                message=f"No feasible (teacher, room, block) for section {sid!r}.",
            )

    model = cp_model.CpModel()
    assign_vars = [model.NewBoolVar(f"a_{i}") for i in range(len(feasible))]

    for sid in section_ids:
        model.Add(sum(assign_vars[i] for i in by_section[sid]) == 1)

    teacher_block_pairs: dict[tuple[str, str], List[int]] = {}
    room_block_pairs: dict[tuple[str, str], List[int]] = {}
    for i, (_s, t, r, b) in enumerate(feasible):
        teacher_block_pairs.setdefault((t, b), []).append(i)
        room_block_pairs.setdefault((r, b), []).append(i)

    for _pair, idxs in teacher_block_pairs.items():
        if len(idxs) > 1:
            model.Add(sum(assign_vars[j] for j in idxs) <= 1)
    for _pair, idxs in room_block_pairs.items():
        if len(idxs) > 1:
            model.Add(sum(assign_vars[j] for j in idxs) <= 1)

    solver = cp_model.CpSolver()
    if time_limit_seconds is not None:
        solver.parameters.max_time_in_seconds = time_limit_seconds

    start = time.perf_counter()
    status = solver.Solve(model)
    wall = time.perf_counter() - start

    st = _cp_status_to_solve_status(status)
    if st not in (SolveStatus.OPTIMAL, SolveStatus.FEASIBLE):
        return SectionPlacementResult(
            status=st if st == SolveStatus.INFEASIBLE else SolveStatus.UNKNOWN,
            solver_wall_time_seconds=wall,
            message=solver.StatusName(status),
        )

    placements: List[SectionPlacement] = []
    for i, (sid, t, r, b) in enumerate(feasible):
        if solver.Value(assign_vars[i]) == 1:
            placements.append(
                SectionPlacement(
                    section_id=sid,
                    teacher_id=t,
                    room_id=r,
                    block_id=b,
                )
            )

    if len(placements) != len(section_ids):
        return SectionPlacementResult(
            status=SolveStatus.UNKNOWN,
            solver_wall_time_seconds=wall,
            message="Solver reported success but placement count mismatch.",
        )

    return SectionPlacementResult(
        status=st,
        placements=tuple(placements),
        objective_value=None,
        solver_wall_time_seconds=wall,
        message="OK",
    )
