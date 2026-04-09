# Class Scheduler

Schedule course sections (time, room, teacher) from structured inputs, then assign students to those sections. Optimization sits behind a clear data model and CSV/Django UI workflows.

---

## Problem statement and scope

### Who uses it

| Role | Relationship to the system |
|------|----------------------------|
| **Scheduling staff** | Primary users: define offerings, constraints, and runs; review and publish schedules. |
| **Faculty** | Provide availability and teaching assignments. |
| **Students** | Their requests are inputs for the enrollment step. |

### What “the schedule” means here

1. Each **section** (a specific offering of a course) gets exactly one **time block**, **room**, and **teacher**, respecting hard constraints (availability, no double-booking).
2. **Student enrollment**—given fixed sections, place students into sections for their requested courses (capacity, no time conflicts, priorities).

---

## Technology Stack (Prerequisites to Run Project):

- Python 3.12+
    - Libraries Used:
        - `django`: For Django app web framework.
        - `ortools`: For solving the student/teacher scheduling.
        - `python-dotenv`: For environment variables (Django credentials).
        - `pytest`: For testing OR-Tools solver.
        - `pytest-django`: For testing Django app.

---

## Steps for Project Setup:

1. Install/create project dependencies if applicable (Python)

2. Clone this repository:
```
git clone https://github.com/lmwalk8/class-scheduler-ai.git
cd class-scheduler-ai
```

3. Create and activate a Python virutal environment:
```
python3 -m venv class_scheduler_env
source class_scheduler_env/bin/activate (Linux/macOS) OR class_scheduler_env\Scripts\activate.bat (Windows)
```

4. Install all required dependencies:
```
pip install -r requirements.txt
```

5. Set up required environment variables:

Create a .env file in the repo root (`class-scheduler-ai/.env`) or under `classScheduler/.env` (the latter overrides the former for duplicate keys). Example:

```
DJANGO_SECRET_KEY=your_django_secret
# Optional: IANA timezone for UI and admin timestamps (default America/New_York)
DJANGO_TIME_ZONE=America/Los_Angeles
```

Valid names are from the [IANA time zone database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) (e.g. `America/Chicago`, `Europe/London`).

---

## Toy dataset (reuse for any testing)

Use one small, hand-maintained set so tests and demos stay stable.

| Asset | Target size | Purpose |
|-------|-------------|---------|
| Courses | 4–6 distinct ids | Enough for multiple sections of the same course. |
| Sections | 6–10 rows to schedule | Each row needs a teacher, room, and time block after solving. |
| Teachers | 3–5 | Overlapping skills so placement is non-trivial. |
| Rooms | 2–4 | Capacities differ slightly. |
| Time blocks | 4–8 | Same day or multiple days; at least one intentional “tight” resource. |
| Availability | Sparse, not universal | Forces tradeoffs (teachers/rooms not free every block). |
| Students | ~14 (adjust in script) | Synthetic roster: `student_id`, `name`, `max_credits` for the enrollment phase. |
| Student requests | 2–4 courses per student | Each row is `(student_id, course_id, priority)`; lower priority number = higher preference. Pattern is seeded so you can reproduce or vary runs. |

**Naming:** Stable string ids (`CS101`, `CS101-A`, `T-001`, `ROOM-201`, `MON-P1`). No real PII—use `student_01`, `student_02`, etc., for toy students and requests.

**Location:** `data/toy/` — CSVs produced by a small generator.

**Generate:** from the repo root, run:

```
python scripts/generate_toy_dataset.py
```

Optional: `--out DIR` (default `data/toy`), `--seed N` (default `42`) for **teacher/room availability** and **which courses each student requests** (not section placement). Files include `courses`, `teachers`, `rooms`, `time_blocks`, `sections_to_schedule`, `section_teacher_options`, `teacher_availability`, `room_availability`, `students`, and `student_requests`.

---

## Student Enrollment Solver (Local)

The scheduling logic lives in **`scheduler_core/`** (Django-free). There are two OR-Tools **CP-SAT** steps:

1. **`solve_section_placement`** (`scheduler_core/section_solver.py`) — assign each section a teacher, room, and time block from availability and section–teacher options.

2. **`solve_student_enrollment`** (`scheduler_core/student_solver.py`) — given placed sections (with block_id and capacity), assign students to sections using course requests and priorities.

### Demo script (minimal hard-coded example)

From the repository root, run:

```
python scripts/student_course_enrollment_solver.py
```

This runs section placement on a tiny two-section example, converts the result with **`placed_sections_from_placement`**, then runs student enrollment and prints assignments. It does not use Django or CSV files.

### Using toy CSV data (optional)

1. Generate files under `data/toy/` (also mentioned in more detail above):

```
python scripts/generate_toy_dataset.py
```

2. In Python, load into solver types with **`scheduler_core.toy_csv`** (`load_section_placement_input`, `load_enrollment_input` after section solve). See **`tests/test_toy_csv_solvers.py`** for a full chain (tests are skipped if `data/toy/` is empty).

---

## Django UI: Generate Schedule

After importing data via **Admin to CSV imports** (or manual entry), staff can run the same OR-Tools pipeline the CLI uses:

1. Create a staff user: `python manage.py createsuperuser` (from `classScheduler/`).
2. Log in at `/admin/`, then open **`/schedule/generate/`** (staff only; unauthenticated users are redirected to log in).
3. Click **Run schedulers & save**. This calls `classSchedulerApp.scheduling_service.run_full_schedule`, which:
   - builds `SectionPlacementInput` from the database (sorted ids for stable solver behavior),
   - runs `solve_section_placement` then `solve_student_enrollment`,
   - clears prior enrollments and section assignments, writes new **`Section.assigned_*`** fields, creates a **`ScheduleRun`**, and bulk-creates **`Enrollment`** rows linked to that run.
4. The result page lists section placements and enrollments for that run.

CLI parity (same DB and same code path): from `classScheduler/`:

```
python manage.py run_schedule
```

Run it twice on the same database. The printed `SECTION` / `ENROLL` lines should match between runs if the data is unchanged (OR-Tools is deterministic for a fixed model).

The script `scripts/student_course_enrollment_solver.py` still uses a hard-coded example, not the database. To compare against toy CSVs, import `data/toy/` into Django first, then use **`run_schedule`** or **`/schedule/generate/`**.

---

## Django UI: Teacher and Student Views

Teachers and students can log in with normal Django accounts and open read-only pages that show their assignments only. This uses optional **`Teacher.user`** and **`Student.user`** links (one-to-one with `AUTH_USER_MODEL`).

### URLs and auth

| What | URL |
|------|-----|
| Log in | **`/accounts/login/`** |
| Log out | POST to **`/accounts/logout/`** (use the **Log out** control in the site nav) |
| Home | **`/`** |
| My teaching schedule | **`/schedule/my/teacher/`** (login required; needs linked `Teacher`) |
| My class schedule | **`/schedule/my/student/`** (login required; needs linked `Student`) |

Django settings used by this flow:

- **`LOGIN_URL`** — `/accounts/login/` (unauthenticated users hitting the “my schedule” URLs are sent here).
- **`LOGIN_REDIRECT_URL`** and **`LOGOUT_REDIRECT_URL`** — `/` (after login or logout).

Built-in auth routes come from **`django.contrib.auth.urls`** (included under **`/accounts/`** in the project URLconf).

### Linking accounts in the admin

1. **Create a user** (does not need to be staff unless they should use the admin or **Generate schedule**):
   - In admin: **Authentication and authorization → Users → Add user**, set username and password; or
   - `python manage.py createsuperuser` for a staff account.
2. **Teachers:** **Class scheduler app for Teachers** → open the teacher row → set **User** to that account (raw id: the user’s numeric **ID** from the Users list). Save.
3. **Students:** **Class scheduler app for Students** → open the student row → set **User** the same way.

Each Django user can link to at most one `Teacher` and at most one `Student` record (separate optional links).

### What each page shows

- **My teaching schedule** — All **`Section`** rows whose **`assigned_teacher`** is the linked teacher, with course, room, and time block (reflects whatever is currently stored after the latest successful scheduling run wrote the database).
- **My class schedule** — **`Enrollment`** rows for the linked student for the **latest successful** **`ScheduleRun`**; if none succeeded yet, the latest run is used. Each row shows section, course, teacher, room, and time block for that enrollment.

The site navigation shows **My teaching schedule** / **My class schedule** when the logged-in user has the corresponding link. The home page repeats those links when applicable.
