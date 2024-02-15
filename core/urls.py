from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name="index"),
    path('signin/', signin, name="signin"),
    path('signup/', signup, name="signup"),
    path('comingsoon/', comingsoon, name="comignsoon"),
]