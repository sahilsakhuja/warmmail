# Generated by Django 3.2.2 on 2021-05-08 13:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("subscribe", "0009_auto_20210508_1322"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscription",
            name="dominentpol",
            field=models.CharField(default="pm25", max_length=100),
            preserve_default=False,
        ),
    ]
