# Generated by Django 5.0.2 on 2024-02-27 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webvideo', '0009_alter_scrollervideo_mask_video'),
    ]

    operations = [
        migrations.AddField(
            model_name='uservideoproject',
            name='error_description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
