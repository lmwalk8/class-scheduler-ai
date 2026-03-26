# Class Scheduler

Schedule course **sections** (time, room, teacher) from structured inputs, then assign students to those sections. Optimization sits behind a clear data model and CSV/Django UI workflows.

---

## Problem statement and scope

### Who uses it

| Role | Relationship to the system |
|------|----------------------------|
| **Scheduling staff / registrar** | Primary users: define offerings, constraints, and runs; review and publish schedules. |
| **Faculty** | Provide availability and teaching assignments; v1 can model this as data even if entered by staff. |
| **Students** | Their **requests** are inputs for the **enrollment** step. |

### What “the schedule” means here

1. Each **section** (a specific offering of a course) gets exactly one **time block**, **room**, and **teacher**, respecting hard constraints (availability, no double-booking).
2. **Student enrollment**—given fixed sections, place students into sections for their requested courses (capacity, no time conflicts, priorities).

---

## Toy dataset (reuse for any testing)

Use one small, hand-maintained set so tests and demos stay stable.

| Asset | Target size | Purpose |
|-------|-------------|---------|
| Courses | 4–6 distinct `course_id`s | Enough for multiple sections of the same course. |
| Sections | 6–10 rows to schedule | Each row needs a teacher, room, and time block after solving. |
| Teachers | 3–5 | Overlapping skills so placement is non-trivial. |
| Rooms | 2–4 | Capacities differ slightly. |
| Time blocks | 4–8 | Same day or multiple days; at least one intentional “tight” resource. |
| Availability | Sparse, not universal | Forces tradeoffs (teachers/rooms not free every block). |

**Naming:** Stable string ids (`CS101`, `CS101-A`, `T-001`, `ROOM-201`, `MON-P1`). No real PII—use `student_01`, `student_02` if you add requests before production.

**Location:** `data/toy/` — CSVs produced by a small generator.

**Generate:** from the repo root, run:

```bash
python3 scripts/generate_toy_dataset.py
```

Optional: `--out DIR` (default `data/toy`), `--seed N` (default `42`) for availability and student-request patterns. Files include `courses`, `teachers`, `rooms`, `time_blocks`, `sections_to_schedule`, `section_teacher_options`, `teacher_availability`, `room_availability`, plus `students` and `student_requests` for a later enrollment phase.
