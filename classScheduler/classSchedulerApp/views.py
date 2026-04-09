from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Enrollment, ScheduleRun, Section, Student, Teacher
from .scheduling_service import run_full_schedule

def home(request):
    return render(request, "classSchedulerApp/home.html")

def _latest_schedule_run_for_display():
    run = (
        ScheduleRun.objects.filter(status=ScheduleRun.Status.SUCCESS)
        .order_by("-created_at")
        .first()
    )
    if run:
        return run
    return ScheduleRun.objects.order_by("-created_at").first()

@staff_member_required
def generate_schedule(request):
    if request.method == "POST":
        run, err = run_full_schedule()
        if err:
            messages.error(request, err)
            return redirect("generate_schedule")
        messages.success(
            request,
            f"Schedule generated successfully (run {run.run_id}).",
        )
        return redirect("schedule_run_detail", pk=run.pk)

    return render(
        request,
        "classSchedulerApp/generate_schedule.html",
        {
            "last_run": ScheduleRun.objects.order_by("-created_at").first(),
        },
    )

@staff_member_required
def schedule_run_detail(request, pk: int):
    run = get_object_or_404(ScheduleRun, pk=pk)
    enrollments = (
        Enrollment.objects.filter(schedule_run=run)
        .select_related("student", "section", "section__course")
        .order_by("student__student_id", "section__section_id")
    )
    sections = (
        Section.objects.filter(assigned_time_block__isnull=False)
        .select_related(
            "course",
            "assigned_teacher",
            "assigned_room",
            "assigned_time_block",
        )
        .order_by("section_id")
    )
    return render(
        request,
        "classSchedulerApp/schedule_run_detail.html",
        {
            "run": run,
            "enrollments": enrollments,
            "sections": sections,
        },
    )

@login_required
def my_teacher_schedule(request):
    teacher = Teacher.objects.filter(user=request.user).first()
    if not teacher:
        messages.info(
            request,
            "Your account is not linked to a teacher profile. Ask an administrator to set "
            "the User field on your Teacher record in the admin.",
        )
        return redirect("home")
    sections = (
        Section.objects.filter(assigned_teacher=teacher)
        .select_related("course", "assigned_room", "assigned_time_block")
        .order_by(
            "assigned_time_block__day_of_week",
            "assigned_time_block__start_time",
            "section_id",
        )
    )
    return render(
        request,
        "classSchedulerApp/my_teacher_schedule.html",
        {
            "teacher": teacher,
            "sections": sections,
        },
    )

@login_required
def my_student_schedule(request):
    student = Student.objects.filter(user=request.user).first()
    if not student:
        messages.info(
            request,
            "Your account is not linked to a student profile. Ask an administrator to set "
            "the User field on your Student record in the admin.",
        )
        return redirect("home")
    run = _latest_schedule_run_for_display()
    enrollments = []
    if run is not None:
        enrollments = (
            Enrollment.objects.filter(student=student, schedule_run=run)
            .select_related(
                "section",
                "section__course",
                "section__assigned_teacher",
                "section__assigned_room",
                "section__assigned_time_block",
            )
            .order_by("section__section_id")
        )
    return render(
        request,
        "classSchedulerApp/my_student_schedule.html",
        {
            "student": student,
            "schedule_run": run,
            "enrollments": enrollments,
        },
    )
