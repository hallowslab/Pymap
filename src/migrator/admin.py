import logging
from django.http import HttpRequest
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.utils.translation import ngettext
from celery.result import AsyncResult
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist

from django_celery_results.models import TaskResult
from .models import CeleryTask, UserPreferences
from .tasks import purge_results, validate_finished
from pymap import celery_app

logger = logging.getLogger(__name__)

# Ignore param type: , see https://github.com/typeddjango/django-stubs/issues/507
class TaskAdmin(admin.ModelAdmin):  # type: ignore
    actions = [
        "archive_selected",
        "admin_validate_finished",
        "admin_purge_results",
    ]
    list_display = ["task_id", "source", "destination", "owner", "start_time"]
    ordering = ["-start_time"]

    @admin.action(description="Archive selected tasks and clear results")
    def archive_selected(
        self, request: HttpRequest, queryset: "QuerySet[CeleryTask]"
    ) -> None:
        for task in queryset:
            try:
                result = AsyncResult(task.task_id, app=celery_app)
                result.get(timeout=5.0)
                result.forget()
            except TimeoutError:
                self.message_user(
                    request,
                    f"Failed to clear results for Task ID: {task.task_id}",
                    messages.WARNING,
                )
            try:
                db_result = TaskResult.objects.get(task_id=task.task_id)
                db_result.delete()
            except ObjectDoesNotExist:
                self.message_user(
                    request,
                    f"No DB result found for task {task.task_id}",
                    messages.WARNING,
                )
            except ImproperlyConfigured:
                self.message_user(
                    request,
                    "Task result backend is not configured for django-db.",
                    messages.WARNING,
                )
                break
            except Exception as e:
                self.message_user(
                    request,
                    f"Error deleting task results: {e}",
                    messages.ERROR,
                )
                continue

        updated = queryset.update(archived=True)
        self.message_user(
            request,
            ngettext(
                "%d task archived.",
                "%d tasks archived.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    @admin.action(description="Validate crashed tasks and set finished flag")
    def admin_validate_finished(
        self, request: HttpRequest, _: "QuerySet[CeleryTask]"
    ) -> None:
        validate_finished.delay()
        self.message_user(
            request, "validate_finished task dispatched.", messages.SUCCESS
        )

    @admin.action(description="Purge finished Celery task results")
    def admin_purge_results(
        self, request: HttpRequest, _: "QuerySet[CeleryTask]"
    ) -> None:
        purge_results.delay(1, 0, 0, finished_field="true")
        self.message_user(request, "purge_results task dispatched.", messages.SUCCESS)


# Ignore param type: , see https://github.com/typeddjango/django-stubs/issues/507
class PreferencesAdmin(admin.ModelAdmin):  # type: ignore
    list_display = ["user", "host_patterns"]
    ordering = ["user"]


# Register only migrator-specific models here
admin.site.register(CeleryTask, TaskAdmin)
admin.site.register(UserPreferences, PreferencesAdmin)
