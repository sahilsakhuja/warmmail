# Generated by Django 3.2 on 2021-04-30 18:08

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("subscribe", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="subscriber",
            name="email_hash",
        ),
        migrations.AddField(
            model_name="subscriber",
            name="confirmed_date",
            field=models.DateTimeField(default=datetime.date(2021, 4, 30)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="subscriber",
            name="created_date",
            field=models.DateTimeField(default=datetime.date(2021, 4, 30)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="subscriber",
            name="temp_token",
            field=models.CharField(default=None, max_length=24),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="subscriber",
            name="verified",
            field=models.BooleanField(default=False),
        ),
    ]
