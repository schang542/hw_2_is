"""
models.py — Data model for AttendanceChimp.

AttendanceChimp is an electronic class attendance tool.  Instructors create
courses and lectures; each lecture is assigned a random QR code.  Students
photograph the QR code and upload the image.  The system decodes the QR code,
matches it to a lecture, and records the attendance.

Entities
--------
- CourseProfile   : extends Django User → instructor-specific data
- StudentProfile  : extends Django User → student-specific data
- Course          : a course taught by one instructor
- Enrollment      : junction table linking students to courses
- Lecture         : a single class meeting (has a QR-code identifier)
- QRCodeUpload    : a student's uploaded QR-code photograph
"""

from django.db import models
from django.contrib.auth.models import User

import logging
import string
import random

logger = logging.getLogger(__name__) # set up tracking, auditing, and debugging
                                                               # allows using logger.warning(), logger.error(), 
                                                               # logger.info(), etc. Better than print() for debuggin... 

# for getUploadsForCourse()
import zoneinfo
CDT = zoneinfo.ZoneInfo("America/Chicago")

# ---------------------------------------------------------------------------
# User profiles
# ---------------------------------------------------------------------------
class InstructorProfile(models.Model):
    """
    Stores profile details for a registered instructor. Instructors can teach 
    many courses. If associated User is deleted, corresponding InstructorProfile 
    instance will be deleted.

    Attributes:
        user (models.OnetoOneField): One-to-one link to Django's Auth User model.
        instructor_id (int): 64-bit auto-incrementing primary key
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=128)
    instructor_id = models.BigAutoField(primary_key=True)

class StudentProfile(models.Model):
    """
    Stores profile details for a registered student. One student can be enrolled
    in multiple courses via Enrollment table, and can submit multiple QR codes.
    If associated User is deleted, corresponding StudentProfile will be deleted.

    Attributes:
        user (models.OnetoOneField): One-to-one link to Django's Auth User model.
        instructor_id (int): 64-bit auto-incrementing primary key
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=128)
    student_id = models.BigAutoField(primary_key=True)

# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------
class Course(models.Model):
    """
    Stores details for a course. Each course is taught by one instructor, and 
    multiple courses can be linked to each student via Enrollment table. Each 
    course is also linked to multiple lectures. If associated InstructorProfile 
    is deleted, corresponding Course instances will be deleted.

    Attributes:
        course_id (int): 64-bit auto-incrementing primary key
        name (str): Name of course
        instructor_id (ForeignKey): A reference to the instructor who teaches 
        the course
        day_mon-day_fri (bool): A boolean value for each meeting day; True if
        meeting that day, False if not, and defaults to False
        start_time (TimeField): Course start time
        end_time (TimeField): Course end time
    """
    course_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    instructor = models.ForeignKey(InstructorProfile, on_delete=models.CASCADE)
    day_mon = models.BooleanField(default=False)
    day_tue = models.BooleanField(default=False)
    day_wed = models.BooleanField(default=False)
    day_thu = models.BooleanField(default=False)
    day_fri = models.BooleanField(default=False)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    # Method to check whether Course meets on a certain day
    def meets_on_day(self, weekday):
        return ((weekday == 0 and self.day_mon) or
        (weekday == 1 and self.day_tue) or
        (weekday == 2 and self.day_wed) or
        (weekday == 3 and self.day_thu) or
        (weekday == 4 and self.day_fri))

# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------
class Enrollment(models.Model):
    """
    Table linking students to courses via many-to-many relationship; one student
    can have multiple courses and vice versa. If associated StudentProfile or
    Course is deleted, corresponding Enrollment instances will be deleted.

    Attributes:
        enrollment_id (int): 64-bit auto-incrementing primary key
        student_id (ForeignKey): A reference to the StudentProfile taking the 
        course
        course_id (ForeignKey): a reference to the course that has the student
    """
    enrollment_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------
class Lecture(models.Model):
    """
    Represents a lecture that is a part of a course. Each lecture is linked to
    one course and one QR code. If associated Course is deleted, all corresponding
    Lecture instances will be deleted.

    Attributes:
        lecture_id (int): 64-bit auto-incrementing primary key
        course_id (ForeignKey): A reference to the Course that the lecture is
        part of
        date (DateTimeField): Date of lecture
        qr_identifier (str): A single string identifying that Lecture's QR code
    """
    lecture_id = models.BigAutoField(primary_key=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    qr_identifier = models.CharField(max_length=100, unique=True)

# ---------------------------------------------------------------------------
# QR Code Upload
# ---------------------------------------------------------------------------
class QRCodeUpload(models.Model):
    """
    Represents photos uploaded by a student, each associated with a StudentProfile
    and optionally a Lecture. If associated StudentProfile is deleted, all
    corresponding QRCodeUpload instances will be deleted. If associated Lecture
    deleted, all corresponding QRCode instances will be set to NULL to prevent
    full loss of QRCode.

    Attributes:
        qrcode_id (int): 64-bit auto-incrementing primary key
        student_id (ForeignKey): A reference to the StudentProfile that is 
        uploading the QRCode
        lecture_id (nullable ForeignKey): An optional reference to the Lecture
        that the QRCode is being submitted to; if none given, set to NULL
        image (FileField): The uploaded QR code image, saved to folder qr_codes
        uploaded_at (DateTimeField): Date and time that QR code was uploaded,
        to check that uploaded at same time as lecture
    """
    qrcode_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    image = models.FileField(upload_to='qr_codes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

# ---------------------------------------------------------------------------
# Helper / API functions
# ---------------------------------------------------------------------------
def get_username(user):
    """
    Helper function that prints user's username if logged in; otherwise prints
    "User not found"
    """
    if user and user.is_authenticated:
        print(user.get_username())
    else:
        print("User not found")

def getUploadsForCourse(course):
    try:
        full_course = Course.objects.get(name=course)
    except Course.DoesNotExist:
        return []

    all_uploads = QRCodeUpload.objects.filter(
        lecture__course__name=course
    )

    valid_uploads = []
    for upload in all_uploads:
        timezone = upload.uploaded_at.astimezone(CDT)
        day = timezone.weekday()
        time = timezone.time()
        if (full_course.meets_on_day(day) 
        and full_course.start_time <= time <= full_course.end_time):
            valid_uploads.append(upload)
    return valid_uploads


