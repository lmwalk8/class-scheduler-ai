# Section placement fields, Enrollment.schedule_run, ScheduleRun metadata.

import uuid

import django.db.models.deletion
from django.db import migrations, models


def _default_run_id():
    return str(uuid.uuid4())


class Migration(migrations.Migration):

    dependencies = [
        ("classSchedulerApp", "0002_csv_import_and_uniques"),
    ]

    operations = [
        migrations.AddField(
            model_name="section",
            name="assigned_teacher",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_sections",
                to="classSchedulerApp.teacher",
            ),
        ),
        migrations.AddField(
            model_name="section",
            name="assigned_room",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_sections",
                to="classSchedulerApp.room",
            ),
        ),
        migrations.AddField(
            model_name="section",
            name="assigned_time_block",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_sections",
                to="classSchedulerApp.timeblock",
            ),
        ),
        migrations.AddField(
            model_name="enrollment",
            name="schedule_run",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="enrollments",
                to="classSchedulerApp.schedulerun",
            ),
        ),
        migrations.AddField(
            model_name="schedulerun",
            name="enrollment_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="schedulerun",
            name="section_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="schedulerun",
            name="error_message",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="schedulerun",
            name="run_id",
            field=models.CharField(
                default=_default_run_id,
                editable=False,
                max_length=64,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="schedulerun",
            name="status",
            field=models.CharField(
                choices=[("success", "Success"), ("failed", "Failed")],
                default="failed",
                max_length=20,
            ),
        ),
    ]
