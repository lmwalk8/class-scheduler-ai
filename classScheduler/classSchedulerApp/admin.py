from django.contrib import admin

from .models import Course, Section, Teacher, Room, TimeBlock, TeacherAvailability, RoomAvailability, SectionTeacherOption, Student, StudentRequest, Enrollment, ScheduleRun

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
