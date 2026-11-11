"""
views.py — HTTP request handlers for AttendanceChimp.

Each view corresponds to one URL endpoint.  Views receive an HTTP request,
interact with the database via models.py, and return an HTTP response.
"""

from django.shortcuts import render, redirect
from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponseBadRequest, JsonResponse)
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from datetime import datetime
import zoneinfo
import json
import io
import uuid

from .models import (InstructorProfile, StudentProfile, Course, Lecture,
                    QRCodeUpload)
# from .models import (InstructorProfile, StudentProfile, Course, Enrollment,
#                      Lecture, QRCodeUpload, is_instructor, is_student,
#                      getUploadsForCourse)

CDT = zoneinfo.ZoneInfo("America/Chicago")


# ---------------------------------------------------------------------------
# HW2  — index, time, sum
# ---------------------------------------------------------------------------
def time_view(request):
    cur_time = datetime.now(CDT)
    return HttpResponse(cur_time.strftime("%H:%M"))

def sum_view(request):
    n1 = request.GET.get('n1')
    n2 = request.GET.get('n2')
    n1 = float(n1)
    n2 = float(n2)

    total = n1 + n2
    # Autograder expects HTTPs not JSON for some reason
    return HttpResponse(f'<p>{total}<p>')

# ---------------------------------------------------------------------------
# HW4  — user creation
# ---------------------------------------------------------------------------
def index(request):
    """Render the home page (index.html) with correct time and logged-in user."""
    now = datetime.now(CDT).strftime("%H:%M")
    context = {
        'current_time': now,
        'user': request.user,
    }
    return render(request, 'app/index.html', context)

def sign_up(request):
    if request.method != 'GET':
        return HttpResponse(status=405)
    return render(request, 'app/new.html')

@csrf_exempt
def createUser(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    user_name = request.POST.get('user_name')
    email = request.POST.get('email')
    password = request.POST.get('password')
    user_type = request.POST.get('is_student')

    if User.objects.filter(email=email).exists():
        return HttpResponse("An account with this email already exists.", status=400)
    
    new_user = User.objects.create_user(
        username=user_name,
        email=email,
        password=password
    )
    if user_type == "1":
        StudentProfile.objects.create(
            user=new_user,
            username=user_name, 
            email=email, 
            password=new_user.password)
    else:
        InstructorProfile.objects.create(
            user=new_user,
            username=user_name, 
            email=email, 
            password=new_user.password)
    login(request, new_user)
    return HttpResponse("Successfully created new user", status=200)


# ---------------------------------------------------------------------------
# HW5  — courses, lectures, QR uploads, dump
# ---------------------------------------------------------------------------
def new_course(request):
    if request.method != 'GET':
        return HttpResponse(status=405)
    if not hasattr(request.user, 'instructorprofile'):
        return HttpResponse("Not logged in as instructor", status=401)
    return render(request, 'app/new_course.html')

@csrf_exempt
def createCourse(request):
    if request.method != 'POST':
        return HttpResponse(status=405)
    if not hasattr(request.user, 'instructorprofile'):
        return HttpResponse("Not logged in as instructor", status=401)

    name = request.POST.get('course-name')
    start = request.POST.get('start-time')
    end = request.POST.get('end-time')
    schedule = ','.join([
        day for day in [
            'day-mon',
            'day-tue',
            'day-wed',
            'day-thu',
            'day-fri'
        ]
        if request.POST.get(day)
    ])

    if Course.objects.filter(name=name).exists():
        return HttpResponse("A course with this name already exists.", status=400)
    
    Course.objects.create(
        name=name,
        instructor_id=request.user.instructorprofile,
        start_time=start,
        end_time=end,
        meeting_schedule=schedule
    )
    return HttpResponse("Successfully created new course", status=200)

def new_lecture(request):
    if request.method != 'GET':
        return HttpResponse(status=405)
    if not hasattr(request.user, 'instructorprofile'):
        return HttpResponse("Not logged in as instructor", status=401)
    return render(request, 'app/new_lecture.html')

@csrf_exempt
def createLecture(request):
    if request.method != 'POST':
        return HttpResponse(status=405)
    if not hasattr(request.user, 'instructorprofile'):
        return HttpResponse("Not logged in as instructor", status=401)

    course = request.POST.get('choice')

    if not Course.objects.get(name=course, instructor_id=request.user.instructorprofile):
        return HttpResponse("No course with this name exists", status=400)
    
    qr_id = str(uuid.uuid4())
    
    Lecture.objects.create(
        course_id=Course.objects.get(name=course),
        qr_identifier=qr_id
    )
    return HttpResponse("Successfully created new lecture", status=200)

def new_qr_upload(request):
    if request.method != 'GET':
        return HttpResponse(status=405)
    if not hasattr(request.user, 'studentprofile'):
        return HttpResponse("Not logged in as student", status=401)
    return render(request, 'app/new_qr_upload.html')

@csrf_exempt
def createQRCodeUpload(request):
    if request.method != 'POST':
        return HttpResponse(status=405)
    if not hasattr(request.user, 'studentprofile'):
        return HttpResponse("Not logged in as student", status=401)

    image = request.FILES.get('imageUpload')
    qr_id = request.POST.get('qr_id')
    lecture = None
    if qr_id:
        lecture = Lecture.objects.filter(qr_identifier=qr_id).first()
    
    QRCodeUpload.objects.create(
        student_id=request.user.studentprofile,
        lecture_id=lecture,
        image=image
    )
    return HttpResponse("Successfully uploaded QR code", status=200)

def dumpUploads(request):
    if request.method != 'GET':
        return HttpResponse(status=405)
    if not hasattr(request.user, 'instructorprofile'):
        return HttpResponse("Not logged in as instructor", status=401)
    qs = QRCodeUpload.objects.select_related('student_id')
    combined = []
    for upload in qs:
        combined.append({
            'username': upload.student_id.username,
            'upload_time': upload.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return JsonResponse(combined, safe=False)

# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------



