import uuid
from django.db import models


class MigrationJob(models.Model):
    JOB_STATUS = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_host = models.CharField(max_length=255)
    dest_host = models.CharField(max_length=255)
    additional_args = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=JOB_STATUS, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Job {self.id} ({self.status})"


class MigrationTask(models.Model):
    TASK_STATUS = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        MigrationJob, related_name="tasks", on_delete=models.CASCADE
    )
    user1 = models.CharField(max_length=255)
    user2 = models.CharField(max_length=255)
    credential_ref = models.CharField(max_length=255)  # temporary cache key
    logfile = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=TASK_STATUS, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
