# Generated manually for teacher/student login links.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("classSchedulerApp", "0003_schedule_glue"),
    ]

    operations = [
        migrations.AddField(
            model_name="teacher",
            name="user",
            field=models.OneToOneField(
                blank=True,
                help_text="Link a login account so this teacher can open “My teaching schedule”.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="teacher_profile",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="student",
            name="user",
            field=models.OneToOneField(
                blank=True,
                help_text="Link a login account so this student can open “My class schedule”.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="student_profile",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
