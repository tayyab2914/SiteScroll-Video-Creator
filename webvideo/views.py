from django.shortcuts import render, redirect
from django.contrib import messages
import csv
from urllib.parse import urlparse
from .models import *
from .task import *
from django.contrib.auth.decorators import login_required
import time
from django.http import HttpResponse, FileResponse
import os


@login_required(login_url='/signin')
def download_video(request, video_id):
    try:
        scroll_video_instance = ScrollerVideo.objects.get(id=video_id,user=request.user)
    except Exception as e:
        return redirect('/snip/dashboard/')


    video_filename = scroll_video_instance.output_video_path.name
    download_filename="output_video.mp4"
    video_path = os.path.join(settings.MEDIA_ROOT, 'output_videos', video_filename)
    if os.path.exists(video_path):
        with open(video_path, 'rb') as video_file:
            response = HttpResponse(video_file.read(), content_type='video/mp4')
            response['Content-Disposition'] = f'attachment; filename="{download_filename}"'
            return response
    else:
        return redirect('/snip/dashboard/')


@login_required(login_url='/signin')
def project(request, id):
    context={}
    user_videos = UserVideoProject.objects.filter(id=id)
    if not user_videos.exists():
        return redirect('/snip/dashboard/')
    user_videos = user_videos.first()
    if not user_videos.user == request.user:
        return redirect('/snip/dashboard')
    scroller_video = ScrollerVideo.objects.filter(mask_video=user_videos)
    context['scroller_video'] = scroller_video
    return render(request, 'pages/project.html', context)

@login_required(login_url='/signin')
def delete_project(request, id):
    try:
        user_video = UserVideoProject.objects.get(id=id, user=request.user)
    except Exception as e:
        messages.error(request, "Unauthenticated")
        return redirect('/snip/dashboard/')
    user_video.delete()
    messages.success(request, "Project deleted successfully!")
    return redirect('/snip/dashboard/')


@login_required(login_url='/signin')
def dashboard(request):
    context={}
    current_user = request.user
    video_projects = UserVideoProject.objects.filter(user=request.user)
    if video_projects.exists():
        context['video_projects'] = video_projects
    return render(request, 'pages/dashboard.html',context)
    
@login_required(login_url='/signin')
def makevideo(request):
    if request.method=="POST":

        allowed_projects = 5
        user_video = UserVideoProject.objects.filter(user=request.user)
        print(user_video.count())
        if user_video.count() >= allowed_projects:
            messages.error(request, f"You cannot create more than {allowed_projects} projects!")
            return redirect('/snip/dashboard/')

        csv_file = request.FILES.get('CsvFileLinks')
        video_file = request.FILES.get('videoFile')
        text_links = request.POST.get('textLinks')

        ALLOWED_VIDEO_EXTENSIONS = {'mp4'}
        if video_file is None:
            messages.error(request, "Please upload a video.")
        else:
            videofile_extension = video_file.name.split('.')[-1]
            if not videofile_extension in ALLOWED_VIDEO_EXTENSIONS:
                messages.error(request, f"Invalid video file format. {ALLOWED_VIDEO_EXTENSIONS} format supported!")
                return render(request, 'pages/makevideo.html')

        links = []    
        if csv_file is None:
            links = text_links.split(',')
            if not any(links):
                messages.error(request, "Please upload a CSV or enter links.")
        else:
            if not csv_file.name.endswith('.csv'):
                messages.error(request, "Invalid file format. Please upload a CSV file.")
            else:
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                csv_reader = csv.reader(decoded_file)
                
                for row in csv_reader:
                    links.extend(row)
                if not links:
                    messages.error(request, "Your CSV file is empty!")
        

        # Validate each link
        links_valid = True
        if any(links):
            for link in links:
                if not is_valid_link(link):
                    messages.error(request, f'Invalid link format: {link}')
                    links_valid = False

            if links_valid:
                user_video = UserVideoProject(mask_video_path=video_file,user=request.user, project_state='Draft')
                user_video.save()
                mask_video_path = output_path = os.path.join(settings.MEDIA_ROOT, 'mask_videos', user_video.mask_video_path.path)
                video_clip = VideoFileClip(mask_video_path)
                video_clip_duration = video_clip.duration

                if video_clip_duration > 601:
                    return render(request, 'pages/makevideo.html')
                for link in links:
                    scroller_video = ScrollerVideo(user=request.user, web_url=link, mask_video=user_video)
                    scroller_video.save()

                user_video_id = user_video.id
                return render(request, 'pages/makevideo.html', {'user_video_id':user_video_id})

    return render(request, 'pages/makevideo.html')



def generate_videos_for_links(request):
    
    user_video_id = request.GET.get('user_video_id')
    video_width = request.GET.get('video_width')
    video_height = request.GET.get('video_height')
    mask_radius = request.GET.get('mask_radius')
    mask_width = request.GET.get('mask_width')

    # Convert parameters to appropriate types if needed (e.g., int)
    user_video_id = int(user_video_id) if user_video_id else None
    video_width = int(video_width) if video_width else None
    video_height = int(video_height) if video_height else None
    mask_radius = int(mask_radius) if mask_radius else None
    mask_width = int(mask_width) if mask_width else None

    user_video = UserVideoProject.objects.filter(id=user_video_id)
    if not user_video.exists():
        return HttpResponse("Video Project not exist!")
    user_video = user_video.first()
    if not user_video.user==request.user:
        return HttpResponse("Video Project Unauthenticated!")
    
    if user_video.project_state == 'In Progress':
        return redirect(f'/snip/project/{user_video.id}/')

    user_video.project_state = 'In Progress'
    user_video.save()
    scroll_videos = ScrollerVideo.objects.filter(mask_video=user_video)
    try:
        for scroll_video_instance in scroll_videos:
            screenshot_path = take_screenshot(scroller_video_instance=scroll_video_instance, url=scroll_video_instance.web_url, width=video_width, height=video_height)
            scrolling_video = scroll_screenshot(screenshot_path=screenshot_path, mask_path=scroll_video_instance.mask_video.mask_video_path.path, scrolling_width=video_width, scrolling_height=video_height)
            output_path = create_mask_and_merge(scroll_video=scrolling_video, mask_path=scroll_video_instance.mask_video.mask_video_path.path, mask_radius=mask_radius, mask_width=mask_width)

            scroll_video_instance.output_video_path = output_path
            scroll_video_instance.is_ready = True
            scroll_video_instance.save()

        user_video.project_state = 'Completed'
        user_video.save()
    except Exception as e:
        print(e)
        user_video.project_state = 'Error'
        messages.error(request, f'Error: {e}')
    return HttpResponse("Video Project Completed!")


def is_valid_link(link):
    try:
        parsed_url = urlparse(link)
        return all([parsed_url.scheme, parsed_url.netloc])
    except ValueError:
        return False
