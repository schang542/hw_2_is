"""
LLM used: ChatGPT (Free version)
Prompt (copied directly from HW documentation):
Your diagram should show all entities, their attributes, and the relationships between them:
• InstructorProfile / StudentProfile tables (instead of one Users table – think why. . . )
• Course table with at least name, instructor, meeting schedule
• Enrollment table: links students to courses (many-to-many)
• Lecture table: linked to a course, has a date and a QR identifier
• QRCodeUpload table: linked to a student and (optionally) a lecture

Define Django model classes for each table from the ER
diagram (see Django documentation / class slides). Write a detailed doc string and, if applicable,
helper functions.
"""

import uuid

from django.db import models
from django.core.exceptions import ValidationError


class InstructorProfile(models.Model):
    """
    Stores the profile and identifying information of an instructor.

    Each instructor can teach multiple courses. The relationship between
    InstructorProfile and Course is one-to-many: each Course references
    one instructor, while an instructor may have zero or more courses.

    Attributes:
        first_name: Instructor's first name.
        last_name: Instructor's last name.
        email: Unique email address used to identify the instructor.
        department: Academic department to which the instructor belongs.

    Relationships:
        One InstructorProfile can be associated with multiple Course
        records through Course.instructor.

    Notes:
        Django automatically creates an integer primary key named id
        unless another primary key is explicitly defined.
    """

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)

    def __str__(self):
        """Return the instructor's full name."""
        return f"{self.first_name} {self.last_name}"


class StudentProfile(models.Model):
    """
    Stores the profile and identifying information of a student.

    A student can enroll in several courses and upload multiple
    QR-code images. The Enrollment model represents the many-to-many
    relationship between students and courses.

    Attributes:
        first_name: Student's first name.
        last_name: Student's last name.
        email: Unique email address identifying the student.
        student_number: Unique institutional student identifier.
        program: Academic program in which the student is enrolled.

    Relationships:
        A StudentProfile has zero or more Enrollment records and
        zero or more QRCodeUpload records.

    Design:
        Student-specific attributes are kept separate from instructor
        attributes to avoid mixing different role-specific data.
    """

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    student_number = models.CharField(max_length=30, unique=True)
    program = models.CharField(max_length=100)

    def __str__(self):
        """Return the student's name and student number."""
        return f"{self.first_name} {self.last_name} ({self.student_number})"

    def get_enrolled_courses(self):
        """Return all courses in which this student is enrolled."""
        return Course.objects.filter(
            enrollments__student=self
        ).distinct()


class Course(models.Model):
    """
    Represents a course taught by an instructor.

    Each course has a name, a unique course code, a meeting schedule,
    and one assigned instructor. A course can have many enrolled
    students and many lecture sessions.

    Attributes:
        name: Human-readable course name.
        course_code: Unique identifier for the course.
        instructor: Foreign key to InstructorProfile.
        meeting_schedule: Description of regular meeting days and times.
        created_at: Timestamp indicating when the course was created.

    Relationships:
        Many-to-one with InstructorProfile.
        One-to-many with Lecture.
        Many-to-many with StudentProfile through Enrollment.

    Notes:
        meeting_schedule is stored as text for flexibility. A more
        advanced scheduling system could use a separate model for
        meeting days, start times, end times, and locations.
    """

    name = models.CharField(max_length=200)
    course_code = models.CharField(max_length=20, unique=True)

    instructor = models.ForeignKey(
        InstructorProfile,
        on_delete=models.PROTECT,
        related_name="courses",
    )

    meeting_schedule = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return the course code and name."""
        return f"{self.course_code}: {self.name}"

    def get_enrolled_students(self):
        """Return all students enrolled in this course."""
        return StudentProfile.objects.filter(
            enrollments__course=self
        ).distinct()

    def get_lectures(self):
        """Return this course's lectures ordered by date."""
        return self.lectures.order_by("lecture_date")


class Enrollment(models.Model):
    """
    Represents a student's enrollment in a course.

    This model resolves the many-to-many relationship between
    StudentProfile and Course. Each record links exactly one student
    to exactly one course.

    Attributes:
        student: Foreign key to the enrolled student.
        course: Foreign key to the selected course.
        enrolled_at: Date and time when enrollment was recorded.

    Relationships:
        Many-to-one with StudentProfile.
        Many-to-one with Course.

    Constraints:
        A student cannot have duplicate enrollment records for the
        same course. A unique database constraint enforces this rule.
    """

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )

    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="unique_student_course_enrollment",
            )
        ]

    def __str__(self):
        """Describe the student-course enrollment."""
        return f"{self.student} enrolled in {self.course}"

    def clean(self):
        """Validate the student-course pairing."""
        super().clean()

        if self.student_id and self.course_id:
            # Add additional enrollment rules here if needed.
            pass


class Lecture(models.Model):
    """
    Represents an individual lecture session belonging to a course.

    Every lecture has a scheduled date and a unique QR identifier.
    The identifier can be encoded into a QR code displayed during
    the lecture so that uploaded images can be matched to a session.

    Attributes:
        course: Foreign key to the course hosting the lecture.
        lecture_date: Date and time of the lecture.
        qr_identifier: Unique UUID used to identify the lecture's QR code.
        created_at: Timestamp indicating when the lecture was created.

    Relationships:
        Many-to-one with Course.
        One-to-many with QRCodeUpload; uploads may optionally reference
        a particular lecture.

    Notes:
        The UUID identifies the lecture but does not itself generate
        an image. QR image generation can be implemented separately.
    """

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lectures",
    )

    lecture_date = models.DateTimeField()

    qr_identifier = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return the course and lecture date."""
        return f"{self.course.course_code} - {self.lecture_date}"

    def get_uploads(self):
        """Return all QR-code uploads associated with this lecture."""
        return self.qr_uploads.all()


class QRCodeUpload(models.Model):
    """
    Stores a QR-code image uploaded by a student.

    Each upload belongs to one student and may optionally be associated
    with a lecture. The optional lecture relationship supports uploads
    that have not yet been matched to a particular session.

    Attributes:
        student: Foreign key to the student who submitted the upload.
        lecture: Optional foreign key to the associated lecture.
        image: Uploaded image file containing a QR code.
        uploaded_at: Timestamp indicating when the upload was created.
        status: Processing state of the uploaded image.

    Relationships:
        Many-to-one with StudentProfile.
        Optional many-to-one with Lecture.

    Notes:
        ImageField requires Pillow and an appropriate Django media-file
        configuration. File storage is separate from database storage.

        The status field records the processing state; actual QR-code
        scanning and validation must be implemented separately.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="qr_uploads",
    )

    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="qr_uploads",
    )

    image = models.ImageField(upload_to="qr_uploads/")

    uploaded_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    def __str__(self):
        """Return the upload identifier and submitting student."""
        return f"Upload {self.pk} by {self.student}"

    def mark_processed(self, lecture=None):
        """
        Mark this upload as successfully processed.

        Args:
            lecture: Optional Lecture instance identified by QR scanning.

        Raises:
            ValidationError: If the supplied lecture is not an instance
                of Lecture or if the student is not enrolled in the
                lecture's course.

        Notes:
            This helper updates database fields. It does not scan the
            image or verify that its contents match the lecture QR code.
        """
        if lecture is not None:
            if not isinstance(lecture, Lecture):
                raise ValidationError(
                    "lecture must be a Lecture instance."
                )

            if not Enrollment.objects.filter(
                student=self.student,
                course=lecture.course,
            ).exists():
                raise ValidationError(
                    "The student is not enrolled in this lecture's course."
                )

            self.lecture = lecture

        self.status = self.Status.PROCESSED
        self.save(update_fields=["lecture", "status"])

