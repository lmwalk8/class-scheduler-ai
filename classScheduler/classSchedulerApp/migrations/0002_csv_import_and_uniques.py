# Generated manually for CsvImport model and natural-key uniqueness.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("classSchedulerApp", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="course",
            name="course_id",
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name="section",
            name="section_id",
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name="teacher",
            name="teacher_id",
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name="room",
            name="room_id",
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name="timeblock",
            name="block_id",
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name="student",
            name="student_id",
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AddConstraint(
            model_name="teacheravailability",
            constraint=models.UniqueConstraint(
                fields=("teacher", "time_block"),
                name="uniq_teacher_time_block",
            ),
        ),
        migrations.AddConstraint(
            model_name="roomavailability",
            constraint=models.UniqueConstraint(
                fields=("room", "time_block"),
                name="uniq_room_time_block",
            ),
        ),
        migrations.AddConstraint(
            model_name="sectionteacheroption",
            constraint=models.UniqueConstraint(
                fields=("section", "teacher"),
                name="uniq_section_teacher_option",
            ),
        ),
        migrations.AddConstraint(
            model_name="studentrequest",
            constraint=models.UniqueConstraint(
                fields=("student", "course"),
                name="uniq_student_course_request",
            ),
        ),
        migrations.AddConstraint(
            model_name="enrollment",
            constraint=models.UniqueConstraint(
                fields=("student", "section"),
                name="uniq_student_section_enrollment",
            ),
        ),
        migrations.CreateModel(
            name="CsvImport",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "import_kind",
                    models.CharField(
                        choices=[
                            ("courses", "courses.csv"),
                            ("teachers", "teachers.csv"),
                            ("rooms", "rooms.csv"),
                            ("time_blocks", "time_blocks.csv"),
                            ("sections", "sections_to_schedule.csv"),
                            (
                                "section_teacher_options",
                                "section_teacher_options.csv",
                            ),
                            (
                                "teacher_availability",
                                "teacher_availability.csv",
                            ),
                            ("room_availability", "room_availability.csv"),
                            ("students", "students.csv"),
                            ("student_requests", "student_requests.csv"),
                        ],
                        max_length=40,
                    ),
                ),
                ("file", models.FileField(upload_to="csv_imports/%Y/%m/")),
                (
                    "status",
                    models.CharField(default="pending", max_length=20),
                ),
                ("message", models.TextField(blank=True)),
                (
                    "rows_imported",
                    models.PositiveIntegerField(default=0),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
            ],
            options={
                "verbose_name": "CSV import",
                "verbose_name_plural": "CSV imports",
                "ordering": ["-created_at"],
            },
        ),
    ]
