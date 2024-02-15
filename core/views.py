from django.shortcuts import render, redirect

def index(request):
    return render(request, 'pages/landing.html')

def signin(request):
    return render(request, 'pages/signin.html')

def signup(request):
    return render(request, 'pages/signup.html')
