# Generated by Django 3.2 on 2021-04-30 18:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("subscribe", "0003_auto_20210430_1855"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subscription",
            name="status",
            field=models.IntegerField(default=1, max_length=1),
        ),
    ]
