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

from .models import (InstructorProfile, StudentProfile)
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
    return render(request, 'app/new')

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
    if user_type == 1:
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



# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------



