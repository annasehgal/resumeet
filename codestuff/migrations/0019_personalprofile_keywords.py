# Generated by Django 4.2.16 on 2024-10-20 05:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('codestuff', '0018_personalprofile_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='personalprofile',
            name='keywords',
            field=models.ManyToManyField(blank=True, to='codestuff.keywords'),
        ),
    ]
