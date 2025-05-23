# Generated by Django 5.0.7 on 2024-11-17 18:28

import migrator.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("migrator", "0007_remove_userpreferences_dark_mode_enabled_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="celerytask",
            name="custom_label",
            field=models.CharField(default="", max_length=255),
        ),
        migrations.AlterField(
            model_name="userpreferences",
            name="host_patterns",
            field=models.JSONField(default=migrator.models.host_patterns_default),
        ),
    ]
