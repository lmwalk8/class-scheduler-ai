from django.contrib import admin

from .csv_import import run_import
from .models import (
    Course,
    CsvImport,
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

@admin.register(CsvImport)
class CsvImportAdmin(admin.ModelAdmin):
    list_display = (
        "import_kind",
        "status",
        "rows_imported",
        "created_at",
    )
    list_filter = ("import_kind", "status")
    readonly_fields = ("status", "message", "rows_imported", "created_at")
    fieldsets = (
        (
            None,
            {
                "fields": ("import_kind", "file"),
                "description": (
                    "Choose the dataset type that matches your CSV columns "
                    "(same layout as data/toy/ from generate_toy_dataset.py). "
                    "Import order: courses, teachers, rooms, time_blocks, sections, "
                    "section_teacher_options, teacher_availability, room_availability, "
                    "students, student_requests."
                ),
            },
        ),
        (
            "Result",
            {
                "fields": ("status", "message", "rows_imported", "created_at"),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        should_run = not change or (form is not None and "file" in form.changed_data)
        if not should_run or not obj.file:
            return
        try:
            obj.file.open("rb")
            try:
                n = run_import(obj.import_kind, obj.file)
            finally:
                obj.file.close()
            obj.status = "success"
            obj.message = f"Imported {n} row(s)."
            obj.rows_imported = n
        except Exception as exc:
            obj.status = "error"
            obj.message = str(exc)
            obj.rows_imported = 0
        obj.save(update_fields=["status", "message", "rows_imported"])

admin.site.register(Course)
admin.site.register(Section)
admin.site.register(Teacher)
admin.site.register(Room)
admin.site.register(TimeBlock)
admin.site.register(TeacherAvailability)
admin.site.register(RoomAvailability)
admin.site.register(SectionTeacherOption)
admin.site.register(Student)
admin.site.register(StudentRequest)
admin.site.register(Enrollment)
admin.site.register(ScheduleRun)
