"""
CSV import for toy dataset layouts (see scripts/generate_toy_dataset.py).

Each public import_* function returns the number of rows written (created or updated).
"""

from __future__ import annotations

import csv
from datetime import datetime
from io import TextIOWrapper
from typing import BinaryIO, Iterable

from django.db import transaction

from .models import (
    Course,
    Room,
    Section,
    SectionTeacherOption,
    Student,
    StudentRequest,
    Teacher,
    TeacherAvailability,
    TimeBlock,
    RoomAvailability,
)

def _parse_time(value: str):
    value = (value or "").strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Invalid time value: {value!r}")


def _read_dict_rows(fileobj: BinaryIO) -> list[dict[str, str]]:
    text = TextIOWrapper(fileobj, encoding="utf-8", newline="")
    try:
        reader = csv.DictReader(text)
        if not reader.fieldnames:
            return []
        rows = []
        for raw in reader:
            row = {k: (v.strip() if isinstance(v, str) else v) for k, v in raw.items() if k}
            rows.append(row)
        return rows
    finally:
        text.detach()


def import_courses(rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for row in rows:
        course_id = row.get("course_id", "").strip()
        if not course_id:
            continue
        Course.objects.update_or_create(
            course_id=course_id,
            defaults={
                "title": row.get("title", "").strip() or course_id,
                "credits": int(row.get("credits", 0) or 0),
            },
        )
        n += 1
    return n


def import_teachers(rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for row in rows:
        teacher_id = row.get("teacher_id", "").strip()
        if not teacher_id:
            continue
        Teacher.objects.update_or_create(
            teacher_id=teacher_id,
            defaults={
                "name": row.get("name", "").strip() or teacher_id,
                "email": row.get("email", "").strip() or "unknown@example.com",
            },
        )
        n += 1
    return n


def import_rooms(rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for row in rows:
        room_id = row.get("room_id", "").strip()
        if not room_id:
            continue
        Room.objects.update_or_create(
            room_id=room_id,
            defaults={
                "capacity": int(row.get("capacity", 0) or 0),
                "room_type": row.get("room_type", "").strip() or "lecture",
            },
        )
        n += 1
    return n


def import_time_blocks(rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for row in rows:
        block_id = row.get("block_id", "").strip()
        if not block_id:
            continue
        TimeBlock.objects.update_or_create(
            block_id=block_id,
            defaults={
                "day_of_week": row.get("day_of_week", "").strip() or "?",
                "start_time": _parse_time(row.get("start_time", "")),
                "end_time": _parse_time(row.get("end_time", "")),
            },
        )
        n += 1
    return n


def import_sections(rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for row in rows:
        section_id = row.get("section_id", "").strip()
        course_key = row.get("course_id", "").strip()
        if not section_id or not course_key:
            continue
        course = Course.objects.filter(course_id=course_key).first()
        if not course:
            raise ValueError(f"Unknown course_id {course_key!r} for section {section_id!r}")
        Section.objects.update_or_create(
            section_id=section_id,
            defaults={
                "course": course,
                "min_enrollment": int(row.get("min_enrollment", 0) or 0),
                "max_enrollment": int(row.get("max_enrollment", 0) or 0),
            },
        )
        n += 1
    return n


def import_section_teacher_options(rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for row in rows:
        sid = row.get("section_id", "").strip()
        tid = row.get("teacher_id", "").strip()
        if not sid or not tid:
            continue
        section = Section.objects.filter(section_id=sid).first()
        if not section:
            raise ValueError(f"Unknown section_id {sid!r}")
        teacher = Teacher.objects.filter(teacher_id=tid).first()
        if not teacher:
            raise ValueError(f"Unknown teacher_id {tid!r}")
        SectionTeacherOption.objects.get_or_create(section=section, teacher=teacher)
        n += 1
    return n


def import_teacher_availability(rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for row in rows:
        tid = row.get("teacher_id", "").strip()
        bid = row.get("block_id", "").strip()
        if not tid or not bid:
            continue
        teacher = Teacher.objects.filter(teacher_id=tid).first()
        if not teacher:
            raise ValueError(f"Unknown teacher_id {tid!r}")
        time_block = TimeBlock.objects.filter(block_id=bid).first()
        if not time_block:
            raise ValueError(f"Unknown block_id {bid!r}")
        TeacherAvailability.objects.get_or_create(teacher=teacher, time_block=time_block)
        n += 1
    return n


def import_room_availability(rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for row in rows:
        rid = row.get("room_id", "").strip()
        bid = row.get("block_id", "").strip()
        if not rid or not bid:
            continue
        room = Room.objects.filter(room_id=rid).first()
        if not room:
            raise ValueError(f"Unknown room_id {rid!r}")
        time_block = TimeBlock.objects.filter(block_id=bid).first()
        if not time_block:
            raise ValueError(f"Unknown block_id {bid!r}")
        RoomAvailability.objects.get_or_create(room=room, time_block=time_block)
        n += 1
    return n


def import_students(rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for row in rows:
        student_id = row.get("student_id", "").strip()
        if not student_id:
            continue
        Student.objects.update_or_create(
            student_id=student_id,
            defaults={
                "name": row.get("name", "").strip() or student_id,
                "max_credits": int(row.get("max_credits", 0) or 0),
            },
        )
        n += 1
    return n


def import_student_requests(rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for row in rows:
        student_key = row.get("student_id", "").strip()
        course_key = row.get("course_id", "").strip()
        if not student_key or not course_key:
            continue
        student = Student.objects.filter(student_id=student_key).first()
        if not student:
            raise ValueError(f"Unknown student_id {student_key!r}")
        course = Course.objects.filter(course_id=course_key).first()
        if not course:
            raise ValueError(f"Unknown course_id {course_key!r}")
        priority = int(row.get("priority", 0) or 0)
        StudentRequest.objects.update_or_create(
            student=student,
            course=course,
            defaults={"priority": priority},
        )
        n += 1
    return n

IMPORT_KIND_HANDLERS = {
    "courses": import_courses,
    "teachers": import_teachers,
    "rooms": import_rooms,
    "time_blocks": import_time_blocks,
    "sections": import_sections,
    "section_teacher_options": import_section_teacher_options,
    "teacher_availability": import_teacher_availability,
    "room_availability": import_room_availability,
    "students": import_students,
    "student_requests": import_student_requests,
}

def run_import(kind: str, fileobj: BinaryIO) -> int:
    if kind not in IMPORT_KIND_HANDLERS:
        raise ValueError(f"Unknown import kind: {kind!r}")
    rows = _read_dict_rows(fileobj)
    handler = IMPORT_KIND_HANDLERS[kind]
    with transaction.atomic():
        return handler(rows)
