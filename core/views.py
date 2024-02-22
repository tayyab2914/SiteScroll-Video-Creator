from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, logout, login
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.mail import send_mail
import random
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.decorators import login_required

def index(request):
    return render(request, 'pages/landing.html')

def signin(request):
    if request.method=="POST":
        email = request.POST.get('email')
        username = email
        password = request.POST.get('password')

        user = User.objects.filter(username=email)
        if user.exists():
            user = user.first()
            auth_user = authenticate(username=user.username, password=password)
            if auth_user is None:
                messages.error(request, "Invalid username or password")
            else:
                # messages.success(request, "User Authenticated!")
                login(request, auth_user)
                return redirect('/snip/dashboard/')
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'pages/signin.html')


def is_exist_email(email):
    is_exist = User.objects.filter(username=email).exists()
    return is_exist


def signup(request):
    context={}
    if request.method == 'POST':
        email = request.POST.get('email')
        username = email
        first_name = request.POST.get('firstname')
        last_name = request.POST.get('lastname')
        password = request.POST.get('password')
        code = request.POST.get('code')
        if code:
            if code == request.session.get('verification_code'):
                email = request.session.get('email')
                username = request.session.get('username')
                first_name = request.session.get('first_name')
                last_name = request.session.get('last_name')
                password = request.session.get('password')
                user = User.objects.create_user(username=username, email=email, first_name=first_name, last_name=last_name, password=password)
                del request.session['email']
                del request.session['verification_code']
                del request.session['username']
                del request.session['first_name']
                del request.session['last_name']
                del request.session['password']
                login(request, user)
                # messages.success(request, "User has registered successfuly!")
                return redirect('/snip/dashboard/')
            else:
                context['code_send'] = False
                messages.error(request, "Incorrect Verification code!")
        else:
            if is_exist_email(email):
                messages.error(request, "Email already exist!")
            else:
                request.session['email'] = email
                request.session['username'] = username
                request.session['first_name'] = first_name
                request.session['last_name'] = last_name
                request.session['password'] = password
                context['code_send'] = True
                send_verification_code(request, email)
                messages.success(request, "Verification code has been sent")
            
    return render(request, 'pages/signup.html', context)

def send_verification_code(request, client_email):
    verification_code = ''.join(random.choices('1234567890', k=6))
    request.session['verification_code'] = verification_code
    subject = "Verification Code"
    message = f'Your verification code is: {verification_code}'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [client_email]
    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    except Exception as e:
        print(e)


@login_required(login_url='/signin')
def signout(request):
    logout(request)
    return redirect('/')

def comingsoon(request):
    return render(request, 'pages/comingsoon.html')