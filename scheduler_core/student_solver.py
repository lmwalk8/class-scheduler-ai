"""
Student enrollment with OR-Tools CP-SAT.

Assumes sections are already placed (each has course_id, block_id, capacity).
Assigns students to sections to respect capacity, one section per requested course,
and no two enrollments in the same time block for one student.
"""

from __future__ import annotations

import time
from typing import Dict, List, Tuple

from ortools.sat.python import cp_model

from scheduler_core.types import (
    EnrollmentAssignment,
    EnrollmentInput,
    EnrollmentResult,
    PlacedSection,
    SolveStatus,
    StudentSpec,
)

def _cp_status_to_solve_status(status: int) -> SolveStatus:
    if status == cp_model.OPTIMAL:
        return SolveStatus.OPTIMAL
    if status == cp_model.FEASIBLE:
        return SolveStatus.FEASIBLE
    if status == cp_model.INFEASIBLE:
        return SolveStatus.INFEASIBLE
    return SolveStatus.UNKNOWN

def _student_index_map(students: Tuple[StudentSpec, ...]) -> Dict[str, int]:
    return {s.student_id: i for i, s in enumerate(students)}

def _candidate_weights(problem: EnrollmentInput) -> Dict[Tuple[int, int], int]:
    """
    (student_idx, section_idx) -> weight for objective (higher = more preferred).

    Weight uses request priority: lower ``priority`` in CSV means higher preference.
    """
    st_map = _student_index_map(problem.students)
    placed: Tuple[PlacedSection, ...] = problem.placed_sections
    cand: Dict[Tuple[int, int], int] = {}

    for req in problem.requests:
        si = st_map.get(req.student_id)
        if si is None:
            continue
        for sec_idx, sec in enumerate(placed):
            if sec.course_id != req.course_id:
                continue
            # Large base so differences in priority dominate; lower priority int => higher score
            w = 10_000 - req.priority
            key = (si, sec_idx)
            cand[key] = max(cand.get(key, 0), w)
    return cand

def solve_student_enrollment(
    problem: EnrollmentInput,
    *,
    time_limit_seconds: float | None = 30.0,
) -> EnrollmentResult:
    """
    Maximize weighted satisfaction of course requests subject to:

    - at most one section per (student, requested course),
    - no two sections in the same ``block_id`` for one student,
    - section enrollment count <= ``max_enrollment``.
    """
    if not problem.students:
        return EnrollmentResult(
            status=SolveStatus.FEASIBLE,
            enrollments=(),
            message="No students.",
        )

    st_map = _student_index_map(problem.students)
    for req in problem.requests:
        if req.student_id not in st_map:
            return EnrollmentResult(
                status=SolveStatus.INVALID,
                message=f"Request references unknown student_id {req.student_id!r}.",
            )

    placed = problem.placed_sections
    if not placed:
        if not problem.requests:
            return EnrollmentResult(
                status=SolveStatus.FEASIBLE,
                enrollments=(),
                message="No sections and no requests.",
            )
        return EnrollmentResult(
            status=SolveStatus.INFEASIBLE,
            message="No placed sections but requests exist.",
        )

    if not problem.requests:
        return EnrollmentResult(
            status=SolveStatus.FEASIBLE,
            enrollments=(),
            message="No requests to satisfy.",
        )

    cand = _candidate_weights(problem)
    if not cand:
        return EnrollmentResult(
            status=SolveStatus.INFEASIBLE,
            message="No matching section for any request (course mismatch).",
        )

    model = cp_model.CpModel()
    y: Dict[Tuple[int, int], cp_model.BoolVar] = {}
    objective_terms: list[cp_model.LinearExpr] = []

    for (si, sec_idx), w in cand.items():
        var = model.NewBoolVar(f"y_s{si}_sec{sec_idx}")
        y[(si, sec_idx)] = var
        objective_terms.append(w * var)

    if objective_terms:
        model.Maximize(sum(objective_terms))

    seen_sc: set[tuple[int, str]] = set()
    for req in problem.requests:
        si = st_map[req.student_id]
        cid = req.course_id
        if (si, cid) in seen_sc:
            continue
        seen_sc.add((si, cid))
        sec_indices = [j for j, sec in enumerate(placed) if sec.course_id == cid]
        vars_for_course = [y[(si, j)] for j in sec_indices if (si, j) in y]
        if vars_for_course:
            model.Add(sum(vars_for_course) <= 1)

    # No double-booking: same block for one student
    block_to_sections: Dict[str, List[int]] = {}
    for j, sec in enumerate(placed):
        block_to_sections.setdefault(sec.block_id, []).append(j)

    for si in range(len(problem.students)):
        for _bid, sec_idxs in block_to_sections.items():
            vars_same_block = [y[(si, j)] for j in sec_idxs if (si, j) in y]
            if len(vars_same_block) > 1:
                model.Add(sum(vars_same_block) <= 1)

    # Capacity
    for sec_idx, sec in enumerate(placed):
        vars_in_section = [y[(si, sec_idx)] for si in range(len(problem.students)) if (si, sec_idx) in y]
        if vars_in_section:
            model.Add(sum(vars_in_section) <= sec.max_enrollment)

    solver = cp_model.CpSolver()
    if time_limit_seconds is not None:
        solver.parameters.max_time_in_seconds = time_limit_seconds

    start = time.perf_counter()
    status = solver.Solve(model)
    wall = time.perf_counter() - start

    st = _cp_status_to_solve_status(status)
    if st not in (SolveStatus.OPTIMAL, SolveStatus.FEASIBLE):
        return EnrollmentResult(
            status=st if st == SolveStatus.INFEASIBLE else SolveStatus.UNKNOWN,
            solver_wall_time_seconds=wall,
            message=solver.StatusName(status),
        )

    out: List[EnrollmentAssignment] = []
    for (si, sec_idx), var in y.items():
        if solver.Value(var) == 1:
            sid = problem.students[si].student_id
            out.append(
                EnrollmentAssignment(
                    student_id=sid,
                    section_id=placed[sec_idx].section_id,
                )
            )

    obj_val: int | None = None
    if objective_terms:
        obj_val = int(solver.ObjectiveValue())

    return EnrollmentResult(
        status=st,
        enrollments=tuple(out),
        objective_value=obj_val,
        solver_wall_time_seconds=wall,
        message="OK",
    )
