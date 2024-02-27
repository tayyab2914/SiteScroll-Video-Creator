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
    parsed_url = urlparse(scroll_video_instance.web_url)
    netloc_parts = parsed_url.netloc.split('.')
    subdomain = netloc_parts[0] if netloc_parts[0] else ''
    domain = '.'.join(netloc_parts[1:]) if len(netloc_parts) > 1 else ''
    download_filename = subdomain + '.' + domain + '.mp4'
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
    error_description = user_videos.error_description
    scroller_video = ScrollerVideo.objects.filter(mask_video=user_videos)
    if not error_description is None:
        context['error_description'] = error_description
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
    ALLOWED_VIDEO_EXTENSIONS = {'mp4'}
    ALLOWED_VIDEO_SIZE = 100  # in mbs
    ALLOWED_VIDEO_PROJECTS = 5
    ALLOWED_VIDEO_DURATION = 600 # in seconds
    ALLOWED_LINKS_COUNT = 100
    links_notice = [f'Maximum Allowed count links: {ALLOWED_LINKS_COUNT}']
    videos_notice = [f'Allowed video extensions: {ALLOWED_VIDEO_EXTENSIONS}', f'Maximum video duration allowed: {int(ALLOWED_VIDEO_DURATION/60)} minutes']
    videos_notice += [f'Maximum video size allowed: {ALLOWED_VIDEO_SIZE} mbs']
    context = {'links_notice':links_notice, 'videos_notice':videos_notice}

    if request.method=="POST":
        csv_file = request.FILES.get('CsvFileLinks')
        video_file = request.FILES.get('videoFile')
        text_links = request.POST.get('textLinks')

        links = perform_validation_on_links(request, csv_file, text_links, ALLOWED_LINKS_COUNT, ALLOWED_VIDEO_PROJECTS)
        if not links:
            return render(request, 'pages/makevideo.html', context)
        
        user_video_project = perform_validation_on_video(request, video_file, ALLOWED_VIDEO_EXTENSIONS, ALLOWED_VIDEO_SIZE, ALLOWED_VIDEO_DURATION)
        if not user_video_project:
            return render(request, 'pages/makevideo.html', context)

        for link in links:
            scroller_video = ScrollerVideo(user=request.user, web_url=link, mask_video=user_video_project)
            scroller_video.save()

        user_video_id = user_video_project.id
        return render(request, 'pages/makevideo.html', {'user_video_id':user_video_id})

    return render(request, 'pages/makevideo.html', context)




# < --- Validation for Links -->

def perform_validation_on_links(request, csv_file, text_links, allowed_links_count, allowed_video_projects):

    if not validate_project_counts(request.user, allowed_video_projects):
        messages.error(request, f"You cannot create more than {allowed_video_projects} projects!")
        return False
    
    if csv_file and not csv_file.name.endswith('.csv'):
        messages.error(request, "Invalid file format. Please upload a CSV file.")
        return False

    links = is_exist_or_get_links(csv_file, text_links)
    if not links:
        messages.error(request, "Please upload a CSV or enter links.")
        return False
    
    if len(links) > allowed_links_count:
        messages.error(request, f"Maximum of {allowed_links_count} links allowed")
        return False
    
    if not validate_links(links):
        messages.error(request, "Invalid link detected!")
        return False
    
    return links


def is_exist_or_get_links(csv_file, text_links):
    links = []
    if csv_file is None:
        links = text_links.split(',')
        if not any(links):
            return False
    else:
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        csv_reader = csv.reader(decoded_file)
        
        for row in csv_reader:
            links.extend(row)
        if not links:
            return False
    return links


def validate_links(links):
    for link in links:
        if not is_valid_link(link):
            return False
    return True

def is_valid_link(link):
    try:
        parsed_url = urlparse(link)
        return all([parsed_url.scheme, parsed_url.netloc])
    except ValueError:
        return False




# < --- Validation for Videos -->

def perform_validation_on_video(request, video_file , allowed_video_extensions, allowed_video_size, allowed_video_duration):

    if not video_file:
        messages.error(request, "No video file uploaded!")
        return False

    if not validate_video_extension(video_file, allowed_video_extensions):
        messages.error(request, f"Invalid video file format. {allowed_video_extensions} format supported!")
        return False

    if not validate_video_size(video_file, allowed_video_size):
        messages.error(request, f"Max file size allowed is {allowed_video_size} mbs")
        return False

    user_video_project =  validate_video_duration(request.user, video_file, allowed_video_duration)
    if not user_video_project:
        messages.error(request, f"Maximum video duration is: {allowed_video_duration}")
    
    return user_video_project


def validate_project_counts(current_user, allowed_project_count):
    user_video_project = UserVideoProject.objects.filter(user=current_user)
    if user_video_project.count() >= allowed_project_count:
        return False
    else:
        return True
    
def validate_video_size(video_file, allowed_video_size):
    video_size = video_file.size
    video_size = video_size / 1048576       # This will get size in mbs
    if video_size > allowed_video_size:
        return False
    else:
        return True
    

def validate_video_extension(video_file, allowed_video_extensions):
    videofile_extension = video_file.name.split('.')[-1]
    if not videofile_extension in allowed_video_extensions:
        return False
    else:
        return True
    

def validate_video_duration(current_user, video_file,  allowed_video_duration):
    user_video_project = UserVideoProject(mask_video_path=video_file,user=current_user, project_state='Draft')
    user_video_project.save()
    mask_video_path = os.path.join(settings.MEDIA_ROOT, 'mask_videos', user_video_project.mask_video_path.path)
    video_clip = VideoFileClip(mask_video_path)
    video_clip_duration = video_clip.duration
    if video_clip_duration > allowed_video_duration:
        user_video_project.delete()
        return False
    else:
        return user_video_project





def generate_videos_for_links(request):
    
    user_video_id = request.GET.get('user_video_id')
    video_width = request.GET.get('video_width')
    video_height = request.GET.get('video_height')

    # Convert parameters to appropriate types if needed (e.g., int)
    user_video_id = int(user_video_id) if user_video_id else None
    video_width = int(video_width) if video_width else None
    video_height = int(video_height) if video_height else None

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
            output_path = create_mask_and_merge(scroll_video=scrolling_video, mask_path=scroll_video_instance.mask_video.mask_video_path.path)

            scroll_video_instance.output_video_path = output_path
            scroll_video_instance.is_ready = True
            scroll_video_instance.save()

        user_video.project_state = 'Completed'
        user_video.save()
    except Exception as e:
        print(e)
        user_video.error_description = e
        user_video.project_state = 'Error'
        user_video.save()
    return HttpResponse("Video Project Completed!")



