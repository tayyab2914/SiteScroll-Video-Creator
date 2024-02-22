from django.urls import path, include
from .views import *

urlpatterns = [
    path('', index, name="index"),
    path('signin/', signin, name="signin"),
    path('signup/', signup, name="signup"),
    path('signout/', signout, name="signout"),
    path('comingsoon/', comingsoon, name="comignsoon"),
    path('snip/', include('webvideo.urls')),
]