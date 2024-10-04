# Generated by Django 5.0.7 on 2024-09-18 23:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("migrator", "0006_celerytask_terminated"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="userpreferences",
            name="dark_mode_enabled",
        ),
        migrations.AddField(
            model_name="userpreferences",
            name="host_patterns",
            field=models.JSONField(default=[["^(vm[0-9]*|vps)", ".example.com"]]),
        ),
    ]
