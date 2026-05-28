import uuid
import os
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class MigrationJob(models.Model):
    JOB_STATUS = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("CHECK", "Check"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_host = models.CharField(max_length=255)
    dest_host = models.CharField(max_length=255)
    additional_args = models.TextField(blank=True, null=True)
    custom_identifier = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=10, choices=JOB_STATUS, default="PENDING")
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Job {self.id} ({self.status})"

    def update_status(self):
        """
        Update the job status based on the status of its tasks.
        """
        task_statuses = list(self.tasks.values_list("status", flat=True))
        if not task_statuses:
            return

        total = len(task_statuses)
        finished_statuses = [s for s in task_statuses if s in ["SUCCESS", "FAILED"]]
        finished_count = len(finished_statuses)

        if finished_count < total:
            # If any task is running or finished, the job is RUNNING
            if any(s in ["RUNNING", "SUCCESS", "FAILED"] for s in task_statuses):
                new_status = "RUNNING"
            else:
                new_status = "PENDING"
        else:
            # All tasks finished
            success_count = finished_statuses.count("SUCCESS")
            failed_count = finished_statuses.count("FAILED")

            if success_count > 0 and failed_count > 0:
                new_status = "CHECK"
            elif success_count == total:
                new_status = "SUCCESS"
            else:
                new_status = "FAILED"

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=["status", "updated_at"])


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
    status = models.CharField(max_length=10, choices=TASK_STATUS, default="PENDING")
    domains = models.TextField(null=True, blank=True)
    start_time = models.DateTimeField(auto_now_add=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    run_time = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    terminated = models.BooleanField(default=False)
    pid = models.IntegerField(null=True, blank=True)
    worker_hostname = models.CharField(max_length=255, null=True, blank=True)
    logfile = models.CharField(max_length=512, null=True, blank=True)

    @property
    def log_path(self):
        if not self.logfile:
            return None
        return os.path.join(settings.ARKA_LOGDIR, "pymap", str(self.job.id), self.logfile)

    @property
    def user1_domain(self):
        if "@" in self.user1:
            return self.user1.split("@")[-1]
        return self.user1

    @property
    def user2_domain(self):
        if "@" in self.user2:
            return self.user2.split("@")[-1]
        return self.user2
