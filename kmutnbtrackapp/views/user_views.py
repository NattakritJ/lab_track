"""
Imports should be grouped in the following order:

1.Standard library imports.
2.Related third party imports.
3.Local application/library specific imports.
"""

import datetime
import re

from django.contrib.auth import logout, login
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.urls import reverse

from kmutnbtrackapp.models import *
from kmutnbtrackapp.views.help import tz, compare_current_time


def home(request):
    if request.GET.get('next'):
        lab_hash = request.GET.get('next')
        if not request.user.is_authenticated:  # check if user do not login
            return HttpResponseRedirect(reverse("kmutnbtrackapp:login", args=(lab_hash,)))
        return HttpResponseRedirect(reverse("kmutnbtrackapp:lab_home", args=(lab_hash,)))
    return render(request, 'Page/LThomepage.html')

def joke(request):
    if request.GET.get('next'):
        lab_hash = request.GET.get('next')
        if not request.user.is_authenticated:  # check if user do not login
            return HttpResponseRedirect(reverse("kmutnbtrackapp:login", args=(lab_hash,)))
        return HttpResponseRedirect(reverse("kmutnbtrackapp:lab_home", args=(lab_hash,)))
    return render(request, 'Page/Jhomepage.html')


def lab_home_page(request, lab_hash):  # this function is used when user get in home page
    if not Lab.objects.filter(hash=lab_hash).exists():  # lab does not exists
        error_message = "QR code ไม่ถูกต้อง"
        return render(request, 'Page/error.html', {"error_message": error_message})

    this_lab = Lab.objects.get(hash=lab_hash)

    if not request.user.is_authenticated:  # if user hasn't login
        lab_name = this_lab.name
        return render(request, 'Page/log_in.html', {"lab_name": lab_name, "lab_hash": lab_hash})
        # render page for logging in in that lab
    else:  # if user already login
        person = Person.objects.get(user=request.user)
        now_datetime = datetime.datetime.now(tz)
        # if have latest history which checkout not at time
        if History.objects.filter(person=person, checkin__lte=now_datetime, checkout__gte=now_datetime).exists():
            last_lab_hist = History.objects.filter(person=person, checkin__lte=now_datetime, checkout__gte=now_datetime)
            last_lab_hist = last_lab_hist[0]

            if last_lab_hist.lab.hash == lab_hash:  # if latest lab is same as the going lab
                return render(request, 'Page/check_out_before_due_new.html',
                              {"last_lab": last_lab_hist.lab,
                               "check_in": last_lab_hist.checkin.astimezone(tz).strftime("%A, %d %b %Y, %H:%M"),
                               "check_out": last_lab_hist.checkout.astimezone(tz).strftime("%A, %d %b %Y, %H:%M")})

            else:  # if latest lab is another lab
                return render(request, 'Page/check_out_prev_lab_before.html',
                              {"last_lab": last_lab_hist.lab, "new_lab": this_lab})

        else:  # goto checkin page
            time_option = compare_current_time()
            midnight_time = now_datetime.replace(hour=23, minute=59, second=59, microsecond=0)
            current_people = History.objects.filter(lab=this_lab, checkout__gte=now_datetime,
                                                    checkout__lte=midnight_time).count()
            return render(request, 'Page/lab_checkin_new.html', {"lab_name": this_lab.name,
                                                                 "lab_hash": this_lab.hash,
                                                                 "time_option": time_option,
                                                                 "time_now_hour": now_datetime.hour,
                                                                 "time_now_minute": now_datetime.minute + 5,
                                                                 "current_people": current_people
                                                                 })  # render page for checkin


def login_api(request):  # api when stranger login
    if request.method == "GET":
        if not request.user.is_authenticated:  # if user hasn't login
            lab_name = ''
            lab_hash = request.GET.get('next', '')
            if lab_hash != '':
                lab_name = Lab.objects.get(hash=lab_hash).name
            return render(request, 'Page/log_in.html', {'lab_hash': lab_hash, 'lab_name': lab_name})
        else:
            return HttpResponseRedirect("/")

    if request.method == "POST":
        lab_hash = request.GET.get('next', '')
        tel_no = request.POST['tel']
        if User.objects.filter(username=tel_no).exists():  # if phone number already in database
            user = User.objects.get(username=tel_no)
            login(request, user,
                  backend='django.contrib.auth.backends.ModelBackend')  # login with username only
            return HttpResponseRedirect(reverse('kmutnbtrackapp:lab_home', args=(lab_hash,)))
        else:  # phone number not in database
            return HttpResponseRedirect(reverse('kmutnbtrackapp:signup', args=(lab_hash,)))


def signup_api(request, lab_hash):  # when stranger click 'Signup and Checkin'
    if request.method == "GET":
        lab_name = Lab.objects.get(hash=lab_hash).name
        return render(request, 'Page/signup_form.html', {'lab_hash': lab_hash, 'lab_name': lab_name, })

    # Receive data from POST
    if request.method == "POST":
        lab_name = Lab.objects.get(hash=lab_hash).name
        tel_no = request.POST["tel"]
        if not re.match(r"[0-9]|\.", tel_no):  # if input is not phone number
            error_message = "รูปแบบเบอร์ไม่ถูกต้อง กรุณาสแกน QR Code ใหม่อีกครั้ง"
            return render(request, 'Page/error.html', {"error_message": error_message})
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        # Form is valid
        if User.objects.filter(username=tel_no).count() != 0:  # if username is already taken
            return render(request, 'Page/signup_form.html', {'lab_hash': lab_hash, 'lab_name': lab_name, 'wrong': 2})
        else:  # if username is available
            # create new User object and save it
            u = User.objects.create(username=tel_no, first_name=first_name, last_name=last_name)
            u.save()
            # create new Person object
            Person.objects.create(user=u, first_name=first_name, last_name=last_name, is_student=False)
            # then login
            login(request, u, backend='django.contrib.auth.backends.ModelBackend')
            return HttpResponseRedirect(reverse('kmutnbtrackapp:lab_home', args=(lab_hash,)))


def logout_api(request):  # api for logging out
    logout(request)
    lab_hash = request.GET.get("lab", None)
    if lab_hash:
        return HttpResponseRedirect(reverse('kmutnbtrackapp:lab_home', args=(lab_hash,)))
    else:
        return HttpResponseRedirect("/")


def check_in(request, lab_hash):  # when user checkin record in history
    person = Person.objects.get(user=request.user)
    this_lab = Lab.objects.get(hash=lab_hash)

    if request.method == "POST":
        checkout_time_str = request.POST['check_out_time']  # get check out time
        now_datetime = datetime.datetime.now(tz)
        midnight_time = now_datetime.replace(hour=23, minute=59, second=59, microsecond=0)

        checkout_datetime = now_datetime.replace(hour=int(checkout_time_str.split(":")[0]),
                                                 minute=int(checkout_time_str.split(":")[
                                                                1]))  # get check out time in object datetime
        if Lab.objects.filter(hash=lab_hash).exists():  # check that lab does exists
            current_people = len(History.objects.filter(lab=this_lab,
                                                        checkout__gte=now_datetime,
                                                        checkout__lte=midnight_time))
            last_lab_hist = History.objects.filter(person=person, checkin__lte=now_datetime, checkout__gte=now_datetime)
            if last_lab_hist.exists():  # if have a history that intersect between now
                if last_lab_hist[0].lab.hash != lab_hash:  # if latest lab is another lab
                    return render(request, 'Page/check_out_prev_lab_before.html',
                                  {"lab_hash_check_out": last_lab_hist[0].lab,
                                   "new_lab": this_lab})
                else:  # if latest lab is same as the going lab
                    last_lab_hist = History.objects.get(person=person, lab=this_lab, checkin__lte=now_datetime,
                                                        checkout__gte=now_datetime)
                    return render(request, 'Page/check_out_before_due_new.html',
                                  {"last_lab": last_lab_hist.lab,
                                   "check_in": last_lab_hist.checkin.astimezone(tz).strftime("%A, %d %b %Y, %H:%M"),
                                   "check_out": last_lab_hist.checkout.astimezone(tz).strftime("%A, %d %b %Y, %H:%M")})
            elif current_people >= this_lab.max_number_of_people:  # if user exceeded lab limit
                new_hist = History.objects.create(person=person,
                                                  lab=this_lab,
                                                  checkin=now_datetime,
                                                  checkout=checkout_datetime)
                return render(request, 'Page/lab_checkin_successful_new.html',
                              {"lab_hash": this_lab.hash,
                               "lab_name": this_lab.name,
                               "exceed_lab_limit": True,
                               "maximum_people": this_lab.max_number_of_people,
                               "check_in": new_hist.checkin.astimezone(tz).strftime("%A, %d %b %Y, %H:%M"),
                               "check_out": new_hist.checkout.astimezone(tz).strftime("%A, %d %b %Y, %H:%M")})
            else:
                new_hist = History.objects.create(person=person,
                                                  lab=this_lab,
                                                  checkin=now_datetime,
                                                  checkout=checkout_datetime)
                return render(request, 'Page/lab_checkin_successful_new.html',
                              {"lab_hash": this_lab.hash,
                               "lab_name": this_lab.name,
                               "check_in": new_hist.checkin.astimezone(tz).strftime("%A, %d %b %Y, %H:%M"),
                               "check_out": new_hist.checkout.astimezone(tz).strftime("%A, %d %b %Y, %H:%M")})
    else:
        error_message = "เซสชั่นหมดอายุ กรุณาสแกน QR Code ใหม่อีกครั้ง"
        return render(request, 'Page/error.html', {"error_message": error_message, "this_lab": this_lab})


def check_out(request, lab_hash):  # api
    person = Person.objects.get(user=request.user)
    out_local_time = datetime.datetime.now(tz)
    log = History.objects.filter(person=person, lab__hash=lab_hash).order_by('checkin').last()
    log.checkout = out_local_time
    log.save()
    if request.GET.get('next_lab'):
        return HttpResponseRedirect(reverse('kmutnbtrackapp:lab_home', args=(request.GET['next_lab'],)))
    return render(request, 'Page/check_out_success.html', {"lab_name": log.lab.name})
