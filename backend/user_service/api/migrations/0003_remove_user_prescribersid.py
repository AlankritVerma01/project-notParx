# Generated by Django 4.1.13 on 2024-03-10 19:00

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0002_user_actionrequired_user_dpass_user_prescribersid"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="prescribersID",
        ),
    ]
