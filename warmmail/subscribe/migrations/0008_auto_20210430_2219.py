# Generated by Django 3.2 on 2021-04-30 22:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("subscribe", "0007_auto_20210430_1937"),
    ]

    operations = [
        migrations.RenameField(
            model_name="subscription",
            old_name="last_email_date",
            new_name="next_email_date",
        ),
        migrations.RemoveField(
            model_name="subscription",
            name="time_of_day",
        ),
        migrations.RemoveField(
            model_name="subscription",
            name="timezone",
        ),
    ]