# Generated by Django 4.2.16 on 2024-10-19 08:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('codestuff', '0003_remove_profile_keywords_profile_keywords'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='community',
            options={'verbose_name_plural': 'Communities'},
        ),
        migrations.AddField(
            model_name='event',
            name='is_active',
            field=models.IntegerField(blank=True, choices=[(1, 'Active'), (0, 'Inactive')], default=1, null=True, verbose_name='Set active?'),
        ),
        migrations.AlterField(
            model_name='community',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
