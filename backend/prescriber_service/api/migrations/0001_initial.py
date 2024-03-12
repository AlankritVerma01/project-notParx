# Generated by Django 4.1.13 on 2024-03-12 05:07

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Prescriber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('firstName', models.CharField(max_length=128)),
                ('lastName', models.CharField(max_length=128)),
                ('province', models.CharField(max_length=128)),
                ('college', models.CharField(max_length=128)),
                ('licenseNum', models.CharField(max_length=128)),
                ('status', models.CharField(max_length=128)),
                ('provDocID', models.CharField(max_length=150, unique=True)),
            ],
        ),
    ]
