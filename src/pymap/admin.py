import logging
from typing import List, Union
from django.http import (
    HttpRequest,
    JsonResponse,
)
from django.conf import settings
from django.urls import URLPattern, URLResolver, path
from django.template.response import TemplateResponse
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied
from django.utils.html import escape


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

from migrator.models import CeleryTask, UserPreferences
from migrator.tasks import purge_results, validate_finished, get_running_tasks
from pymap import celery_app

logger = logging.getLogger(__name__)

# Register your models here.


class CustomAdminSite(AdminSite):
    site_title: str = "Pymap site admin"
    site_header: str = "Pymap administration"
    index_title: str = "Pymap administration"

    def get_urls(self) -> List[Union[URLPattern, URLResolver]]:
        """
        Returns the list of URL patterns for the custom admin site, including additional
        commands for task management.

        The returned list includes both the default admin URLs and custom endpoints for
        rendering the commands page, fetching running tasks, and dispatching Celery task
        operations such as validating finished tasks and purging results.
        """
        urls = super().get_urls()
        custom_urls: list[URLResolver | URLPattern] = [
            path("commands/", self.admin_view(self.task_view), name="commands"),
            path(
                "commands/running-tasks",
                self.admin_view(self.fetch_running_tasks),
                name="running-tasks",
            ),
            path(
                "commands/validate-finished",
                self.admin_view(self.validate_finished),
                name="validate-finished",
            ),
            path(
                "commands/purge-results",
                self.admin_view(self.purge_results),
                name="purge-results",
            ),
            path(
                "config",
                self.admin_view(self.print_config),
                name="config"
            ),
        ]
        logger.debug("Custom admin loaded URLS: %s", custom_urls + urls)
        return custom_urls + urls

    def fetch_running_tasks(self, request: HttpRequest) -> JsonResponse:
        """
        Returns a JSON response with the list of currently running Celery tasks.

        If an error occurs while retrieving the tasks, returns a JSON response with error details and a 400 status code.
        """
        logger.debug("Fetch Running Tasks")
        try:
            tasks = get_running_tasks()
            return JsonResponse({"data": tasks})
        except Exception as e:
            logger.critical("Unhandled exception: %s", e.__str__(), exc_info=True)
            return JsonResponse(
                {"error": "DJANGO:Unhandled exception", "data": e.__str__()}, status=400
            )

    def validate_finished(self, request: HttpRequest) -> JsonResponse:
        """
        Queues the Celery task to validate finished tasks and returns a JSON response.

        Returns:
            JsonResponse: A response indicating the task was queued, or an error message with status 500 if dispatch fails.
        """
        try:
            validate_finished.delay()
            return JsonResponse({"status": "queued"})
        except Exception as e:
            logger.exception("Error in validate_finished")
            return JsonResponse({"error": str(e)}, status=500)

    def purge_results(self, request: HttpRequest) -> JsonResponse:
        """
        Queues the Celery task to purge finished task results and returns a JSON response.

        If the task is successfully queued, returns a JSON object with status "queued".
        If an error occurs, returns a JSON object with the error message and HTTP 500 status.
        """
        try:
            purge_results.delay(1, 0, 0, finished_field="true")
            return JsonResponse({"status": "queued"})
        except Exception as e:
            logger.exception("Error in purge_results")
            return JsonResponse({"error": str(e)}, status=500)

    def task_view(self, request: HttpRequest) -> (TemplateResponse):
        """
        Renders the admin commands page template.

        Returns:
            TemplateResponse: The rendered 'admin/commands.html' page with admin context.
        """
        context = dict(
            self.each_context(request),
        )
        return TemplateResponse(request, "admin/commands.html", context)

    def print_config(self, request: HttpRequest) -> TemplateResponse:
        """
        Admin view to display Django settings in a safe way.
        Sensitive keys are masked.

        Requires "Config Manager" group to access
        """
        if not request.user.groups.filter(name="Config manager").exists():
            raise PermissionDenied("You do not have permission to view this page.")
        SENSITIVE_KEYS = {"SECRET", "PASSWORD", "TOKEN", "KEY"}
        ILLEGAL_KEYS = ["CELERY_BROKER_URL", "DATABASES"]

        config_data = {}
        for key in dir(settings):
            if key.isupper():
                value = getattr(settings, key)
                # Mask sensitive keys
                if any(s in key for s in SENSITIVE_KEYS) or key in ILLEGAL_KEYS:
                    display_value = "*** MASKED ***"
                else:
                    display_value = repr(value)
                    if len(display_value) > 500:
                        display_value = display_value[:500] + " ... (truncated)"

                config_data[key] = escape(display_value)

        context = {
            "config_data": config_data,
            "title": "Current Django Configuration",
            "opts": None,  # Needed to prevent breadcrumbs errors in admin template
        }

        return TemplateResponse(request, "admin/config.html", context)


custom_admin_site = CustomAdminSite(name="admin")
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
