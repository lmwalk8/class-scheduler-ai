from django.core.management.base import BaseCommand

from classSchedulerApp.models import Enrollment, Section
from classSchedulerApp.scheduling_service import run_full_schedule

class Command(BaseCommand):
    help = (
        "Run section + enrollment solvers against the database (same logic as "
        "/schedule/generate/). Prints placements and enrollments for diffing."
    )

    def handle(self, *args, **options):
        run, err = run_full_schedule()
        if err:
            self.stderr.write(self.style.ERROR(err))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS(f"OK run_id={run.run_id} pk={run.pk}"))
        for s in (
            Section.objects.filter(assigned_time_block__isnull=False)
            .select_related("assigned_teacher", "assigned_room", "assigned_time_block")
            .order_by("section_id")
        ):
            self.stdout.write(
                "SECTION\t"
                f"{s.section_id}\t{s.assigned_teacher.teacher_id}\t"
                f"{s.assigned_room.room_id}\t{s.assigned_time_block.block_id}"
            )
        for e in (
            Enrollment.objects.filter(schedule_run=run)
            .select_related("student", "section")
            .order_by("student__student_id", "section__section_id")
        ):
            self.stdout.write(f"ENROLL\t{e.student.student_id}\t{e.section.section_id}")
