from django.urls import path, include
from .views import *

urlpatterns = [
    path('dashboard/', dashboard, name="dashboard"),
    path('makevideo/', makevideo, name="makevideo"),
    path('generate_videos_for_links/', generate_videos_for_links, name="generate_videos_for_links"),
    path('project/<int:id>/', project, name="project"),    
    path('download_video/<video_filename>/', download_video, name="download_video"),    
]