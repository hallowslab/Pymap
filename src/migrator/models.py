# Create your models here.
import os
import shutil
import logging
from typing import Any
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from celery.result import AsyncResult
from django_celery_results.models import TaskResult


from django.conf import settings

from pymap import celery_app

logger = logging.getLogger(__name__)


# TODO:WIP
# class TaskStatistics(models.Model):
#     total_task_count = models.IntegerField(default=0)
#     total_run_time = models.IntegerField(default=0)

#     def __str__(self):
#         return f"Global Task Statistics"

class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dark_mode_enabled = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.user.username}'s Preferences"


class CeleryTask(models.Model):
    """
    Model for an individual task
    """

    id = models.AutoField(primary_key=True)
    task_id = models.CharField(max_length=255)  # Adjust the max_length as needed
    source = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    log_path = models.CharField(max_length=255)  # Adjust the max_length as needed
    n_accounts = models.IntegerField()
    domains = models.TextField(null=True, blank=True)
    archived = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    start_time = models.DateTimeField(auto_now_add=True, blank=True)
    # end_time = models.DateTimeField(default=0,blank=True)
    results_purged = models.BooleanField(default=False)
    run_time = models.IntegerField(default=0)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE
    )  # Assuming User is the Django User model

    def __str__(self) -> str:
        return (
            f"<ID:{self.id} | TID:{self.task_id}><{self.source} | {self.destination}>"
        )


@receiver(post_delete, sender=CeleryTask)
def delete_related_files(
    sender: CeleryTask, instance: CeleryTask, **kwargs: Any
) -> None:
    log_path = instance.log_path
    # TODO: If using redis as result backend, delete data from redis

    if os.path.exists(log_path):
        # Remove the log path if it still exists
        logger.info("Deleting task directory: %s", log_path)
        shutil.rmtree(log_path)
    else:
        # Log a warning if the path is missing
        logger.warning("The task directory does not exist: %s", log_path)
    try:
        # Since we never called .get() or AsyncResult previously do it now and call forget after
        res = AsyncResult(instance.task_id, app=celery_app)
        logger.debug("Found task: %s", res)
        res.forget()
    except TimeoutError:
        logger.error("Failed to clear results for Task ID:%s", instance.task_id)

    if settings.CELERY_RESULT_BACKEND == "django-db":
        # When django-db is the result backend we need to get the result from the TaskResult model
        # and call delete
        try:
            result = TaskResult.objects.get(task_id=instance.task_id)
            result.delete()
        except ObjectDoesNotExist:
            logger.info(
                "There are no stored result for the task ID: %s", instance.task_id
            )
        except Exception as e:
            logger.critical("Unhandled exception %s", e, exc_info=True)
