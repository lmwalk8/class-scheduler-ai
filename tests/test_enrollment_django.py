from datetime import time

import pytest
from django.test import Client
from django.urls import reverse

from classSchedulerApp.models import (
    Course,
    Enrollment,
    Room,
    RoomAvailability,
    ScheduleRun,
    Section,
    SectionTeacherOption,
    Student,
    StudentRequest,
    Teacher,
    TeacherAvailability,
    TimeBlock,
)

USER_PASSWORD = "password123"

def _seed_minimal_solvable_schedule():
    """
    Same topology as ``scripts/student_course_enrollment_solver.py`` (two CS101 sections,
    two teachers/rooms/blocks, full availability, two students each requesting CS101).
    """
    course = Course.objects.create(course_id="CS101", title="Intro", credits=3)
    b1 = TimeBlock.objects.create(
        block_id="B1",
        day_of_week="Monday",
        start_time=time(9, 0),
        end_time=time(10, 0),
    )
    b2 = TimeBlock.objects.create(
        block_id="B2",
        day_of_week="Tuesday",
        start_time=time(9, 0),
        end_time=time(10, 0),
    )
    r1 = Room.objects.create(room_id="R1", capacity=30, room_type="lecture")
    r2 = Room.objects.create(room_id="R2", capacity=30, room_type="lecture")
    t1 = Teacher.objects.create(teacher_id="T1", name="T One", email="t1@example.com")
    t2 = Teacher.objects.create(teacher_id="T2", name="T Two", email="t2@example.com")

    for t, tb in ((t1, b1), (t1, b2), (t2, b1), (t2, b2)):
        TeacherAvailability.objects.create(teacher=t, time_block=tb)
    for r, tb in ((r1, b1), (r1, b2), (r2, b1), (r2, b2)):
        RoomAvailability.objects.create(room=r, time_block=tb)

    sec_a = Section.objects.create(
        section_id="SEC-A",
        course=course,
        min_enrollment=0,
        max_enrollment=30,
    )
    sec_b = Section.objects.create(
        section_id="SEC-B",
        course=course,
        min_enrollment=0,
        max_enrollment=30,
    )
    SectionTeacherOption.objects.create(section=sec_a, teacher=t1)
    SectionTeacherOption.objects.create(section=sec_b, teacher=t2)

    s1 = Student.objects.create(student_id="S1", name="Student One", max_credits=12)
    s2 = Student.objects.create(student_id="S2", name="Student Two", max_credits=12)
    StudentRequest.objects.create(student=s1, course=course, priority=1)
    StudentRequest.objects.create(student=s2, course=course, priority=1)


@pytest.fixture
def admin_user(django_user_model):
    return django_user_model.objects.create_superuser(
        username="admin_testuser",
        password=USER_PASSWORD,
        email="admin_testuser@example.com",
    )

@pytest.fixture
def test_user(django_user_model):
    return django_user_model.objects.create_user(
        username="testuser",
        password=USER_PASSWORD,
        email="test@example.com",
    )

@pytest.fixture
def teacher(db):
    return Teacher.objects.create(
        teacher_id="T-test-1",
        name="Test Teacher",
        email="teacher@example.com",
    )

@pytest.fixture
def student(db):
    return Student.objects.create(
        student_id="S-test-1",
        name="Test Student",
        max_credits=12,
    )

# Basic authentication tests

@pytest.mark.django_db
def test_admin_auth(admin_user):
    client = Client()
    assert client.login(username=admin_user.username, password=USER_PASSWORD)
    response = client.get(reverse("admin:index"))
    assert response.status_code == 200
    assert "Django administration" in response.content.decode()

@pytest.mark.django_db
def test_teacher_auth():
    client = Client()
    response = client.get(reverse("my_teacher_schedule"))
    assert response.status_code == 302
    assert response.url == reverse("login") + "?next=/schedule/my/teacher/"

@pytest.mark.django_db
def test_student_auth():
    client = Client()
    response = client.get(reverse("my_student_schedule"))
    assert response.status_code == 302
    assert response.url == reverse("login") + "?next=/schedule/my/student/"

@pytest.mark.django_db
def test_home_page():
    client = Client()
    response = client.get(reverse("home"))
    assert response.status_code == 200
    assert "Class Scheduler" in response.content.decode()

# Linked profile tests

@pytest.mark.django_db
def test_logged_in_user_no_profile(test_user):
    client = Client()
    assert client.login(username=test_user.username, password=USER_PASSWORD)
    response = client.get(reverse("home"))
    assert response.status_code == 200
    assert (
        "Your account is not linked to a teacher or student record yet."
        in response.content.decode()
    )

@pytest.mark.django_db
def test_logged_in_user_with_teacher_profile(test_user, teacher):
    """Link an existing User to an existing Teacher (same as admin: set Teacher.user)."""
    teacher.user = test_user
    teacher.save(update_fields=["user"])

    client = Client()
    assert client.login(username=test_user.username, password=USER_PASSWORD)
    response = client.get(reverse("my_teacher_schedule"))
    assert response.status_code == 200
    assert "My teaching schedule" in response.content.decode()

@pytest.mark.django_db
def test_logged_in_user_with_student_profile(test_user, student):
    """Link an existing User to an existing Student (same as admin: set Student.user)."""
    student.user = test_user
    student.save(update_fields=["user"])

    client = Client()
    assert client.login(username=test_user.username, password=USER_PASSWORD)
    response = client.get(reverse("my_student_schedule"))
    assert response.status_code == 200
    assert "My class schedule" in response.content.decode()

# Teacher view test

@pytest.mark.django_db
def test_teacher_schedule_shows_assigned_sections(test_user):
    """User linked as teacher; one placed section appears in the schedule table."""
    course = Course.objects.create(course_id="CS-HAPPY", title="Happy Path", credits=3)
    room = Room.objects.create(room_id="R-HAPPY", capacity=30, room_type="lecture")
    block = TimeBlock.objects.create(
        block_id="B-HAPPY",
        day_of_week="Monday",
        start_time=time(9, 0),
        end_time=time(10, 0),
    )
    teacher = Teacher.objects.create(
        teacher_id="T-HAPPY",
        name="Happy Teacher",
        email="happy.teacher@example.com",
        user=test_user,
    )
    Section.objects.create(
        section_id="SEC-HAPPY",
        course=course,
        min_enrollment=1,
        max_enrollment=30,
        assigned_teacher=teacher,
        assigned_room=room,
        assigned_time_block=block,
    )

    client = Client()
    assert client.login(username=test_user.username, password=USER_PASSWORD)
    response = client.get(reverse("my_teacher_schedule"))
    assert response.status_code == 200
    body = response.content.decode()
    assert "My teaching schedule" in body
    assert "T-HAPPY" in body
    for token in ("SEC-HAPPY", "CS-HAPPY", "R-HAPPY", "B-HAPPY"):
        assert token in body

# Student view test

@pytest.mark.django_db
def test_student_schedule_shows_enrollments_for_latest_run(test_user):
    """User linked as student; enrollment for latest successful run shows section details."""
    course = Course.objects.create(course_id="CS-STU", title="Student Happy", credits=3)
    room = Room.objects.create(room_id="R-STU", capacity=30, room_type="lecture")
    block = TimeBlock.objects.create(
        block_id="B-STU",
        day_of_week="Tuesday",
        start_time=time(10, 0),
        end_time=time(11, 0),
    )
    teacher = Teacher.objects.create(
        teacher_id="T-STU",
        name="Staff Teacher",
        email="staff.teacher@example.com",
    )
    section = Section.objects.create(
        section_id="SEC-STU",
        course=course,
        min_enrollment=1,
        max_enrollment=30,
        assigned_teacher=teacher,
        assigned_room=room,
        assigned_time_block=block,
    )
    student = Student.objects.create(
        student_id="S-HAPPY",
        name="Happy Student",
        max_credits=12,
        user=test_user,
    )
    run = ScheduleRun.objects.create(
        status=ScheduleRun.Status.SUCCESS,
        section_count=1,
        enrollment_count=1,
    )
    Enrollment.objects.create(student=student, section=section, schedule_run=run)

    client = Client()
    assert client.login(username=test_user.username, password=USER_PASSWORD)
    response = client.get(reverse("my_student_schedule"))
    assert response.status_code == 200
    body = response.content.decode()
    assert "My class schedule" in body
    assert run.run_id in body
    assert "Success" in body
    for token in ("SEC-STU", "CS-STU", "T-STU", "R-STU", "B-STU"):
        assert token in body

# Staff view tests

@pytest.mark.django_db
def test_admin_can_open_generate(admin_user):
    client = Client()
    assert client.login(username=admin_user.username, password=USER_PASSWORD)
    response = client.get(reverse("generate_schedule"))
    assert response.status_code == 200
    assert "Generate schedule" in response.content.decode()

@pytest.mark.django_db
def test_non_admin_cannot_open_generate(test_user):
    client = Client()
    assert client.login(username=test_user.username, password=USER_PASSWORD)
    response = client.get(reverse("generate_schedule"))
    assert response.status_code == 302
    assert response.url == reverse("login") + "?next=/schedule/generate/"

@pytest.mark.django_db
def test_admin_post_generate_schedule(admin_user):
    _seed_minimal_solvable_schedule()
    client = Client()
    assert client.login(username=admin_user.username, password=USER_PASSWORD)

    response = client.post(reverse("generate_schedule"), follow=True)
    assert response.status_code == 200
    assert response.redirect_chain

    run = ScheduleRun.objects.order_by("-created_at").first()
    assert run is not None
    assert run.status == ScheduleRun.Status.SUCCESS
    assert run.section_count == 2
    assert run.enrollment_count == 2

    body = response.content.decode()
    assert "Schedule generated successfully" in body
    assert run.run_id in body
    assert "SEC-A" in body and "SEC-B" in body

    sec_a = Section.objects.get(section_id="SEC-A")
    sec_b = Section.objects.get(section_id="SEC-B")
    assert sec_a.assigned_teacher.teacher_id == "T1"
    assert sec_b.assigned_teacher.teacher_id == "T2"
    assert sec_a.assigned_room is not None and sec_b.assigned_room is not None
    assert sec_a.assigned_time_block is not None and sec_b.assigned_time_block is not None

    assert Enrollment.objects.filter(schedule_run=run).count() == 2
    student_ids = set(
        Enrollment.objects.filter(schedule_run=run).values_list(
            "student__student_id", flat=True
        )
    )
    assert student_ids == {"S1", "S2"}
