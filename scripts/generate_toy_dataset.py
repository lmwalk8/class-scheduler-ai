#!/usr/bin/env python3
"""
Generate reproducible toy CSVs for scheduling experiments.

Targets:
  courses 4-6, sections 6-10, teachers 3-5, rooms 2-4, time blocks 4-8,
  sparse teacher/room availability.

"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})

def build_courses() -> list[dict[str, object]]:
    return [
        {"course_id": "CS101", "title": "Intro CS", "credits": 3},
        {"course_id": "CS201", "title": "Data Structures", "credits": 3},
        {"course_id": "MATH150", "title": "Calculus I", "credits": 4},
        {"course_id": "ENG101", "title": "Composition", "credits": 3},
        {"course_id": "STAT200", "title": "Intro Statistics", "credits": 3},
    ]

def build_teachers() -> list[dict[str, object]]:
    return [
        {"teacher_id": "T-001", "name": "Alice Chen", "email": "alice.chen@example.edu"},
        {"teacher_id": "T-002", "name": "Bob Ortiz", "email": "bob.ortiz@example.edu"},
        {"teacher_id": "T-003", "name": "Carol Singh", "email": "carol.singh@example.edu"},
        {"teacher_id": "T-004", "name": "Dan Nguyen", "email": "dan.nguyen@example.edu"},
    ]

def build_rooms() -> list[dict[str, object]]:
    return [
        {"room_id": "ROOM-201", "capacity": 35, "room_type": "lecture"},
        {"room_id": "ROOM-305", "capacity": 22, "room_type": "lecture"},
        {"room_id": "LAB-101", "capacity": 18, "room_type": "lab"},
    ]

def build_time_blocks() -> list[dict[str, object]]:
    return [
        {"block_id": "MON-P1", "day_of_week": "MON", "start_time": "09:00", "end_time": "10:30"},
        {"block_id": "MON-P2", "day_of_week": "MON", "start_time": "11:00", "end_time": "12:30"},
        {"block_id": "TUE-P1", "day_of_week": "TUE", "start_time": "09:00", "end_time": "10:30"},
        {"block_id": "TUE-P2", "day_of_week": "TUE", "start_time": "11:00", "end_time": "12:30"},
        {"block_id": "WED-P1", "day_of_week": "WED", "start_time": "09:00", "end_time": "10:30"},
        {"block_id": "WED-P2", "day_of_week": "WED", "start_time": "11:00", "end_time": "12:30"},
    ]


# Which courses each teacher can teach (overlapping skills).
TEACHER_COURSES: dict[str, tuple[str, ...]] = {
    "T-001": ("CS101", "CS201"),
    "T-002": ("CS101", "CS201", "MATH150"),
    "T-003": ("ENG101", "STAT200"),
    "T-004": ("MATH150", "STAT200"),
}

def build_sections_to_schedule() -> list[dict[str, object]]:
    """Eight sections across five courses (some courses have two sections)."""
    return [
        {"section_id": "CS101-A", "course_id": "CS101", "min_enrollment": 8, "max_enrollment": 32},
        {"section_id": "CS101-B", "course_id": "CS101", "min_enrollment": 8, "max_enrollment": 32},
        {"section_id": "CS201-A", "course_id": "CS201", "min_enrollment": 6, "max_enrollment": 28},
        {"section_id": "CS201-B", "course_id": "CS201", "min_enrollment": 6, "max_enrollment": 28},
        {"section_id": "MATH150-A", "course_id": "MATH150", "min_enrollment": 10, "max_enrollment": 34},
        {"section_id": "ENG101-A", "course_id": "ENG101", "min_enrollment": 12, "max_enrollment": 30},
        {"section_id": "STAT200-A", "course_id": "STAT200", "min_enrollment": 10, "max_enrollment": 30},
        {"section_id": "STAT200-B", "course_id": "STAT200", "min_enrollment": 10, "max_enrollment": 30},
    ]

def build_section_teacher_options() -> list[dict[str, object]]:
    """Every section lists at least one eligible teacher; overlap creates placement choices."""
    section_course = {r["section_id"]: str(r["course_id"]) for r in build_sections_to_schedule()}
    rows: list[dict[str, object]] = []
    for sid, cid in section_course.items():
        for tid, courses in TEACHER_COURSES.items():
            if cid in courses:
                rows.append({"section_id": sid, "teacher_id": tid})
    return rows

def build_teacher_availability(
    block_ids: list[str], rng: random.Random
) -> list[dict[str, object]]:
    """Sparse: each teacher is free on a random subset of blocks (not all)."""
    rows: list[dict[str, object]] = []
    for tid in TEACHER_COURSES:
        k = max(3, min(len(block_ids) - 1, rng.randint(3, len(block_ids) - 1)))
        chosen = sorted(rng.sample(block_ids, k))
        for bid in chosen:
            rows.append({"teacher_id": tid, "block_id": bid})
    return rows

def build_room_availability(block_ids: list[str], room_ids: list[str], rng: random.Random) -> list[dict[str, object]]:
    """Sparse room availability to force tradeoffs."""
    rows: list[dict[str, object]] = []
    for rid in room_ids:
        k = max(3, min(len(block_ids) - 1, rng.randint(3, len(block_ids) - 1)))
        chosen = sorted(rng.sample(block_ids, k))
        for bid in chosen:
            rows.append({"room_id": rid, "block_id": bid})
    return rows

def build_students(n: int = 14) -> list[dict[str, object]]:
    return [
        {"student_id": f"student_{i:02d}", "name": f"Student {i:02d}", "max_credits": 18}
        for i in range(1, n + 1)
    ]

def build_student_requests(rng: random.Random) -> list[dict[str, object]]:
    """Synthetic course requests for a later enrollment phase; priorities 1 = highest."""
    course_ids = [c["course_id"] for c in build_courses()]
    rows: list[dict[str, object]] = []
    for i in range(1, 15):
        sid = f"student_{i:02d}"
        picks = rng.sample(course_ids, k=rng.randint(2, 4))
        for prio, cid in enumerate(picks, start=1):
            rows.append({"student_id": sid, "course_id": cid, "priority": prio})
    return rows

def main() -> None:
    p = argparse.ArgumentParser(description="Write toy scheduling CSVs under data/toy/.")
    p.add_argument(
        "--out",
        type=Path,
        default=Path("data/toy"),
        help="Output directory (default: data/toy)",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=42,
        help="RNG seed for availability and student requests (default: 42)",
    )
    args = p.parse_args()
    out: Path = args.out
    rng = random.Random(args.seed)

    courses = build_courses()
    teachers = build_teachers()
    rooms = build_rooms()
    blocks = build_time_blocks()
    block_ids = [str(b["block_id"]) for b in blocks]
    room_ids = [str(r["room_id"]) for r in rooms]

    sections = build_sections_to_schedule()
    section_opts = build_section_teacher_options()
    ta = build_teacher_availability(block_ids, rng)
    ra = build_room_availability(block_ids, room_ids, rng)
    students = build_students(14)
    requests = build_student_requests(rng)

    write_csv(out / "courses.csv", ["course_id", "title", "credits"], courses)
    write_csv(out / "teachers.csv", ["teacher_id", "name", "email"], teachers)
    write_csv(out / "rooms.csv", ["room_id", "capacity", "room_type"], rooms)
    write_csv(
        out / "time_blocks.csv",
        ["block_id", "day_of_week", "start_time", "end_time"],
        blocks,
    )
    write_csv(
        out / "sections_to_schedule.csv",
        ["section_id", "course_id", "min_enrollment", "max_enrollment"],
        sections,
    )
    write_csv(out / "section_teacher_options.csv", ["section_id", "teacher_id"], section_opts)
    write_csv(out / "teacher_availability.csv", ["teacher_id", "block_id"], ta)
    write_csv(out / "room_availability.csv", ["room_id", "block_id"], ra)
    write_csv(out / "students.csv", ["student_id", "name", "max_credits"], students)
    write_csv(out / "student_requests.csv", ["student_id", "course_id", "priority"], requests)

    print(f"Wrote toy dataset to {out.resolve()}")

if __name__ == "__main__":
    main()
