from selenium import webdriver
from moviepy.editor import *
import numpy as np
import time
import uuid
from django.conf import settings
import os


def take_screenshot(scroller_video_instance, url, width=1200, height=800):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument(f'--window-size={width},{height}')
    
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    
    # Scroll to the bottom of the page to load all content
    total_height = int(driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);"))
    driver.set_window_size(width, total_height)

    screenshot_filename = f"{uuid.uuid4()}.png"
    screenshot_path = os.path.join(settings.MEDIA_ROOT, 'screenshots', screenshot_filename)
    driver.save_screenshot(screenshot_path)
    scroller_video_instance.screenshot_path = screenshot_path
    scroller_video_instance.save()
    driver.quit()
    return screenshot_path


def scroll_screenshot(screenshot_path, mask_path, scrolling_width=1200, scrolling_height=800):

    mask_video = VideoFileClip(mask_path)
    scrolling_duration = mask_video.duration
    img_path = screenshot_path
    clip = ImageClip(img_path)

    # Set custom width and height for the video
    custom_width = scrolling_width
    custom_height = scrolling_height

    bg_clip = ColorClip(size=(custom_width, custom_height), color=[228, 220, 220])

    # Set the desired duration for the video
    desired_duration = scrolling_duration  

    # Calculate the scroll speed based on the desired duration
    scroll_speed = (clip.h - custom_height) / desired_duration

    # Lambda function for scrolling effect without using scroll_effect function
    fl = lambda gf, t: gf(t)[int(scroll_speed * t):int(scroll_speed * t) + custom_height, :]

    clip = clip.fl(fl, apply_to=['mask'])

    video = CompositeVideoClip([bg_clip, clip.set_pos("center")], size=(custom_width, custom_height))

    # Set the total duration to the desired duration
    video.duration = desired_duration

    return video




# Create a circular mask
def circular_mask(frame, center, radius):
    Y, X = np.ogrid[:frame.shape[0], :frame.shape[1]]
    mask = (X - center[0]) ** 2 + (Y - center[1]) ** 2 <= radius ** 2
    result = np.zeros_like(frame)
    result[mask] = frame[mask]
    return result


def create_mask_and_merge(scroll_video, mask_path):

    output_filename = f"{uuid.uuid4()}.mp4"
    # Load your videos
    background_video = scroll_video
    video2 = VideoFileClip(mask_path)

    # Apply circular mask to each frame of video2
    center = (video2.size[0] // 2, video2.size[1] // 2)
    radius = int( min(video2.size[0], video2.size[1]) / 2)
    video2 = video2.fl(lambda gf, t: circular_mask(gf(t), center, radius))


    mask_width = int( min(video2.size[0], video2.size[1]) / 2)
    # Resize video2 and make it circular
    video2 = video2.resize(width=mask_width)  # Adjust the width of the circular video
    video2 = video2.fx(vfx.mask_color, color=(0, 0, 0), thr=0)  # Make the mask black

    # Set the position of video2 in the top right corner
    video2_position = (background_video.size[0] - video2.size[0], 0)

    
    # Composite the videos
    final_clip = CompositeVideoClip([
        background_video.set_position("center"),
        video2.set_position(video2_position)
    ])
    

    # Set the duration of the final clip
    final_clip.duration = background_video.duration

    output_path = os.path.join(settings.MEDIA_ROOT, 'output_videos', output_filename)
    # Write the result to a file
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    return output_path
    

