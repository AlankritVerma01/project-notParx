# Generated by Django 4.1.13 on 2024-03-10 20:08

from django.db import migrations
import djongo.models.fields


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0003_remove_user_prescribersid"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="perscribersID",
            field=djongo.models.fields.JSONField(default=list),
        ),
    ]
