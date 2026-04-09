from django.urls import path

from . import views

urlpatterns = [
    path("generate/", views.generate_schedule, name="generate_schedule"),
    path("run/<int:pk>/", views.schedule_run_detail, name="schedule_run_detail"),
    path("my/teacher/", views.my_teacher_schedule, name="my_teacher_schedule"),
    path("my/student/", views.my_student_schedule, name="my_student_schedule"),
]
