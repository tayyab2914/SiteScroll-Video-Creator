# Generated by Django 5.0.2 on 2024-02-21 15:24

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('webvideo', '0007_uservideoproject_alter_srollervideo_mask_video_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SrollerVideo',
            new_name='ScrollerVideo',
        ),
    ]