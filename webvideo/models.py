from django.db import models
from django.contrib.auth.models import User

class UserVideoProject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mask_video_path = models.FileField(max_length=255, upload_to='mask_videos/')
    project_state = models.CharField(max_length=255)
    
class ScrollerVideo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    web_url = models.URLField()
    mask_video = models.ForeignKey(UserVideoProject, on_delete=models.SET_NULL,null=True, blank=True)
    screenshot_path = models.FileField(max_length=255, upload_to='screenshots/', null=True, blank=True)
    output_video_path = models.FileField(max_length=255, upload_to='output_videos/', null=True, blank=True)
    is_ready = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user} - {self.web_url}' 