"""
Build solver inputs from the ORM and persist section + enrollment results.

Uses ``scheduler_core`` (same engine as ``scripts/student_course_enrollment_solver.py``).
"""

from __future__ import annotations

from django.db import transaction

from .models import (
    Enrollment,
    Room,
    ScheduleRun,
    Section,
    Student,
    StudentRequest,
    Teacher,
    TeacherAvailability,
    RoomAvailability,
    SectionTeacherOption,
    TimeBlock,
)

from scheduler_core.section_solver import solve_section_placement
from scheduler_core.student_solver import solve_student_enrollment
from scheduler_core.types import (
    EnrollmentInput,
    PlacedSection,
    SectionPlacementInput,
    SectionSpec,
    SolveStatus,
    StudentRequestSpec,
    StudentSpec,
    placed_sections_from_placement,
)


def build_section_placement_input_from_db() -> SectionPlacementInput:
    """Stable sort order so CP-SAT matches CLI/script runs on the same data."""
    sections = tuple(
        SectionSpec(
            section_id=s.section_id,
            course_id=s.course.course_id,
            min_enrollment=s.min_enrollment,
            max_enrollment=s.max_enrollment,
        )
        for s in Section.objects.select_related("course").order_by("section_id")
    )
    teacher_ids = tuple(t.teacher_id for t in Teacher.objects.order_by("teacher_id"))
    room_ids = tuple(r.room_id for r in Room.objects.order_by("room_id"))
    block_ids = tuple(b.block_id for b in TimeBlock.objects.order_by("block_id"))
    teacher_availability = frozenset(
        (ta.teacher.teacher_id, ta.time_block.block_id)
        for ta in TeacherAvailability.objects.select_related("teacher", "time_block")
    )
    room_availability = frozenset(
        (ra.room.room_id, ra.time_block.block_id)
        for ra in RoomAvailability.objects.select_related("room", "time_block")
    )
    section_teacher_options = frozenset(
        (sto.section.section_id, sto.teacher.teacher_id)
        for sto in SectionTeacherOption.objects.select_related("section", "teacher")
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


def build_enrollment_input_from_db(
    placed_sections: tuple[PlacedSection, ...],
) -> EnrollmentInput:
    students = tuple(
        StudentSpec(student_id=s.student_id)
        for s in Student.objects.order_by("student_id")
    )
    requests = tuple(
        StudentRequestSpec(
            student_id=sr.student.student_id,
            course_id=sr.course.course_id,
            priority=sr.priority,
        )
        for sr in StudentRequest.objects.select_related("student", "course").order_by(
            "student__student_id", "priority", "course__course_id"
        )
    )
    return EnrollmentInput(
        students=students,
        requests=requests,
        placed_sections=placed_sections,
    )


def run_full_schedule() -> tuple[ScheduleRun | None, str]:
    """
    Run section placement then student enrollment; persist under one ScheduleRun.

    Returns ``(run, "")`` on success, or ``(None, error_message)`` on solver/input failure.
    """
    section_problem = build_section_placement_input_from_db()

    if not section_problem.sections:
        with transaction.atomic():
            Enrollment.objects.all().delete()
            Section.objects.update(
                assigned_teacher=None,
                assigned_room=None,
                assigned_time_block=None,
            )
            run = ScheduleRun.objects.create(
                status=ScheduleRun.Status.SUCCESS,
                section_count=0,
                enrollment_count=0,
            )
        return run, ""

    sec_result = solve_section_placement(section_problem)
    if sec_result.status not in (SolveStatus.OPTIMAL, SolveStatus.FEASIBLE):
        return None, f"Section scheduling: {sec_result.status.value} — {sec_result.message}"

    placed = placed_sections_from_placement(
        sec_result.placements,
        section_problem.sections,
    )
    enroll_problem = build_enrollment_input_from_db(placed)

    if not enroll_problem.requests:
        with transaction.atomic():
            Enrollment.objects.all().delete()
            Section.objects.update(
                assigned_teacher=None,
                assigned_room=None,
                assigned_time_block=None,
            )
            for p in sec_result.placements:
                Section.objects.filter(section_id=p.section_id).update(
                    assigned_teacher=Teacher.objects.get(teacher_id=p.teacher_id),
                    assigned_room=Room.objects.get(room_id=p.room_id),
                    assigned_time_block=TimeBlock.objects.get(block_id=p.block_id),
                )
            run = ScheduleRun.objects.create(
                status=ScheduleRun.Status.SUCCESS,
                section_count=len(sec_result.placements),
                enrollment_count=0,
            )
        return run, ""

    enr_result = solve_student_enrollment(enroll_problem)
    if enr_result.status not in (SolveStatus.OPTIMAL, SolveStatus.FEASIBLE):
        return None, f"Enrollment: {enr_result.status.value} — {enr_result.message}"

    with transaction.atomic():
        Enrollment.objects.all().delete()
        Section.objects.update(
            assigned_teacher=None,
            assigned_room=None,
            assigned_time_block=None,
        )
        run = ScheduleRun.objects.create(
            status=ScheduleRun.Status.SUCCESS,
            section_count=len(sec_result.placements),
            enrollment_count=len(enr_result.enrollments),
        )
        for p in sec_result.placements:
            Section.objects.filter(section_id=p.section_id).update(
                assigned_teacher=Teacher.objects.get(teacher_id=p.teacher_id),
                assigned_room=Room.objects.get(room_id=p.room_id),
                assigned_time_block=TimeBlock.objects.get(block_id=p.block_id),
            )
        rows = []
        for e in enr_result.enrollments:
            rows.append(
                Enrollment(
                    student=Student.objects.get(student_id=e.student_id),
                    section=Section.objects.get(section_id=e.section_id),
                    schedule_run=run,
                )
            )
        Enrollment.objects.bulk_create(rows)

    return run, ""
