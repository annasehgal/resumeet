# Generated by Django 4.2.16 on 2024-10-20 04:49

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('codestuff', '0015_alter_room_slug'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='friend',
            unique_together={('user', 'friend')},
        ),
    ]
