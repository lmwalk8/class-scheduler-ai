from django.db import models


class Course(models.Model):
    course_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=200)
    credits = models.IntegerField()

    def __str__(self):
        return self.course_id

class Section(models.Model):
    section_id = models.CharField(max_length=100, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    min_enrollment = models.IntegerField()
    max_enrollment = models.IntegerField()

    def __str__(self):
        return self.section_id

class Teacher(models.Model):
    teacher_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()

    def __str__(self):
        return self.teacher_id

class Room(models.Model):
    room_id = models.CharField(max_length=100, unique=True)
    capacity = models.IntegerField()
    room_type = models.CharField(max_length=100)

    def __str__(self):
        return self.room_id

class TimeBlock(models.Model):
    block_id = models.CharField(max_length=100, unique=True)
    day_of_week = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return self.block_id

class TeacherAvailability(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    time_block = models.ForeignKey(TimeBlock, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["teacher", "time_block"],
                name="uniq_teacher_time_block",
            ),
        ]

    def __str__(self):
        return f"{self.teacher.name} - {self.time_block.day_of_week} {self.time_block.start_time} - {self.time_block.end_time}"

class RoomAvailability(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    time_block = models.ForeignKey(TimeBlock, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["room", "time_block"],
                name="uniq_room_time_block",
            ),
        ]

    def __str__(self):
        return f"{self.room.room_id} - {self.time_block.day_of_week} {self.time_block.start_time} - {self.time_block.end_time}"

class SectionTeacherOption(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["section", "teacher"],
                name="uniq_section_teacher_option",
            ),
        ]

    def __str__(self):
        return f"{self.section.section_id} - {self.teacher.teacher_id}"

class Student(models.Model):
    student_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    max_credits = models.IntegerField()

    def __str__(self):
        return self.student_id

class StudentRequest(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    priority = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="uniq_student_course_request",
            ),
        ]

    def __str__(self):
        return f"{self.student.student_id} - {self.course.course_id} - {self.priority}"

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "section"],
                name="uniq_student_section_enrollment",
            ),
        ]

    def __str__(self):
        return f"{self.student.student_id} - {self.section.section_id}"

class ScheduleRun(models.Model):
    run_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=100)
    error_message = models.TextField()

    def __str__(self):
        return self.run_id


class CsvImport(models.Model):
    """Staff upload: choose dataset kind and CSV file; import runs on save."""

    class ImportKind(models.TextChoices):
        COURSES = "courses", "courses.csv"
        TEACHERS = "teachers", "teachers.csv"
        ROOMS = "rooms", "rooms.csv"
        TIME_BLOCKS = "time_blocks", "time_blocks.csv"
        SECTIONS = "sections", "sections_to_schedule.csv"
        SECTION_TEACHER_OPTIONS = (
            "section_teacher_options",
            "section_teacher_options.csv",
        )
        TEACHER_AVAILABILITY = (
            "teacher_availability",
            "teacher_availability.csv",
        )
        ROOM_AVAILABILITY = "room_availability", "room_availability.csv"
        STUDENTS = "students", "students.csv"
        STUDENT_REQUESTS = "student_requests", "student_requests.csv"

    import_kind = models.CharField(max_length=40, choices=ImportKind.choices)
    file = models.FileField(upload_to="csv_imports/%Y/%m/")
    status = models.CharField(max_length=20, default="pending")
    message = models.TextField(blank=True)
    rows_imported = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "CSV import"
        verbose_name_plural = "CSV imports"

    def __str__(self):
        return f"{self.get_import_kind_display()} @ {self.created_at}"
