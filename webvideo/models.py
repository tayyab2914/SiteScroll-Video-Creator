from django.db import models
from django.contrib.auth.models import User
import os
from django.db.models.signals import pre_delete
from django.dispatch import receiver

class UserVideoProject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mask_video_path = models.FileField(max_length=255, upload_to='mask_videos/')
    project_state = models.CharField(max_length=255)
    error_description = models.TextField(blank=True, null=True)
    
class ScrollerVideo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    web_url = models.URLField()
    mask_video = models.ForeignKey(UserVideoProject, on_delete=models.CASCADE,null=True, blank=True)
    screenshot_path = models.FileField(max_length=255, upload_to='screenshots/', null=True, blank=True)
    output_video_path = models.FileField(max_length=255, upload_to='output_videos/', null=True, blank=True)
    is_ready = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user} - {self.web_url}' 


@receiver(pre_delete, sender=UserVideoProject)
def delete_project_file(sender, instance, **kwargs):
    if instance.mask_video_path and os.path.isfile(instance.mask_video_path.path):
        os.remove(instance.mask_video_path.path)
    
@receiver(pre_delete, sender=ScrollerVideo)
def delete_scroll_file(sender, instance, **kwargs):
    if instance.screenshot_path and os.path.isfile(instance.screenshot_path.path):
        os.remove(instance.screenshot_path.path)
    if instance.output_video_path and os.path.isfile(instance.output_video_path.path):
        os.remove(instance.output_video_path.path)
    