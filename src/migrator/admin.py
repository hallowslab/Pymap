import logging
from typing import List, Union
from django.http import (
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
    HttpRequest,
    JsonResponse,
)
from django.urls import URLPattern, URLResolver, path
from django.shortcuts import redirect
from django.db.models import QuerySet
from django.template.response import TemplateResponse
from django.contrib import admin, messages
from django.contrib.admin import AdminSite, ModelAdmin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.utils.translation import ngettext
from celery.result import AsyncResult

from django_celery_results.models import TaskResult, GroupResult
from django_celery_results.admin import TaskResultAdmin, GroupResultAdmin
from django_celery_beat.models import (
    SolarSchedule,
    IntervalSchedule,
    ClockedSchedule,
    CrontabSchedule,
    PeriodicTask,
)
from django_celery_beat.admin import (
    PeriodicTaskAdmin,
    ClockedScheduleAdmin,
    CrontabScheduleAdmin,
)

from .models import CeleryTask, UserPreferences
from .tasks import (
    purge_results,
    validate_finished,
    get_running_tasks,
    long_running_test_task,
)
from pymap import celery_app

logger = logging.getLogger(__name__)

# Register your models here.


class TaskAdmin(ModelAdmin):
    actions = [
        "purge_results",
        "validate_finished",
        "archive_selected",
        "finished",
        "terminated",
    ]
    list_display = ["task_id", "source", "destination", "owner", "start_time"]
    ordering = ["-start_time"]

    @admin.action(description="Archive selected tasks")
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
                result = TaskResult.objects.get(task_id=task.task_id)
                result.delete()
            except ObjectDoesNotExist:
                self.message_user(
                    request,
                    f"The result does not seem to exist in our database: {task.task_id}",
                    messages.WARNING,
                )
                continue  # Continue to the next task
            except ImproperlyConfigured:
                # If TaskResult model is not available, log or handle the situation
                self.message_user(
                    request,
                    "Task results backend is not configured to use django-db.",
                    messages.WARNING,
                )
                break  # Exit the loop if the backend is not configured
            except Exception as e:
                # Handle other exceptions
                self.message_user(
                    request,
                    f"An error occurred while deleting task results: {e}",
                    messages.ERROR,
                )
                continue  # Continue to the next task

        # Update the queryset to mark tasks as archived
        updated = queryset.update(archived=True)
        self.message_user(
            request,
            ngettext(
                "%d task was successfully marked as archived.",
                "%d Tasks were successfully marked as archived.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    @admin.action(description="Sets finished to true on tasks that may have crashed")
    def admin_validate_finished(
        self, request: HttpRequest, _: "QuerySet[CeleryTask]"
    ) -> None:
        validate_finished.delay()
        self.message_user(
            request, "Task validate_finished dispatched to worker", messages.SUCCESS
        )

    @admin.action(description="Purges Task results from database")
    def admin_purge_results(
        self, request: HttpRequest, _: "QuerySet[CeleryTask]"
    ) -> None:
        purge_results.delay(1, 0, 0, finished=True)
        self.message_user(
            request, "Task purge_results dispatched to worker", messages.SUCCESS
        )


class PreferencesAdmin(ModelAdmin):
    list_display = ["user", "host_patterns"]
    ordering = ["user"]


class CustomAdminSite(AdminSite):
    site_title: str = "Pymap site admin"
    site_header: str = "Pymap administration"
    index_title: str = "Pymap administration"

    def get_urls(self) -> List[Union[URLPattern, URLResolver]]:
        urls = super().get_urls()
        custom_urls: list[URLResolver | URLPattern] = [
            path("tasks/", self.admin_view(self.task_view), name="tasks"),
            path(
                "tasks/running-tasks",
                self.admin_view(self.fetch_running_tasks),
                name="running-tasks",
            ),
        ]
        logger.debug("Custom admin loaded URLS: %s", custom_urls + urls)
        return custom_urls + urls

    def fetch_running_tasks(self, request: HttpRequest) -> JsonResponse:
        logger.debug("Fetch Running Tasks")
        try:
            tasks = get_running_tasks()
            return JsonResponse({"data": tasks})
        except Exception as e:
            logger.critical("Unhandled exception: %s", e.__str__(), exc_info=True)
            return JsonResponse(
                {"error": "DJANGO:Unhandled exception", "data": e.__str__()}, status=400
            )

    def task_view(
        self, request: HttpRequest
    ) -> (TemplateResponse | HttpResponseRedirect | HttpResponsePermanentRedirect):
        if request.method == "POST":
            if "purge_results" in request.POST:
                purge_results.delay()
            elif "validate_finished" in request.POST:
                validate_finished.delay()
            elif "long_running_test_task" in request.POST:
                long_running_test_task.delay()
            return redirect("admin:tasks")
        context = dict(
            self.each_context(request),
        )
        return TemplateResponse(request, "admin/tasks.html", context)


custom_admin_site = CustomAdminSite(name="admin")
# Custom management models
custom_admin_site.register(CeleryTask, TaskAdmin)
custom_admin_site.register(UserPreferences, PreferencesAdmin)
# Django models, need to be registered with the appropriate admin models from django.contrib.auth.admin
custom_admin_site.register(User, UserAdmin)
custom_admin_site.register(Group, GroupAdmin)
# Celery results, need to be registered with the appropriate admin models from django_celery_results.admin
custom_admin_site.register(TaskResult, TaskResultAdmin)
custom_admin_site.register(GroupResult, GroupResultAdmin)
# Periodic tasks, need to be registered with the appropriate admin models from django_celery_beat.admin
custom_admin_site.register(PeriodicTask, PeriodicTaskAdmin)
custom_admin_site.register(ClockedSchedule, ClockedScheduleAdmin)
custom_admin_site.register(CrontabSchedule, CrontabScheduleAdmin)
# Periodic tasks with no admin models
custom_admin_site.register((SolarSchedule, IntervalSchedule))
# custom_admin_site.register(
#     (SolarSchedule, IntervalSchedule, ClockedSchedule, CrontabSchedule, PeriodicTask)
# )
