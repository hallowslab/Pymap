from django.urls import path, register_converter

from . import views

from .converters import LogfileConverter

register_converter(LogfileConverter, "log")

app_name = "migrator"

urlpatterns = [
    path("", views.index, name="index"),
    path("sync/", views.sync, name="sync"),
    path("tasks/", views.tasks, name="tasks"),
    path("tasks/<str:task_id>/", views.task_details, name="tasks-details"),
    path(
        "tasks/<str:task_id>/<log:filename>/",
        views.log_details,
        name="tasks-log-details",
    ),
    path(
        "tasks/<str:task_id>/<log:filename>/download/",
        views.download_log,
        name="tasks-log-download",
    ),
    path(
        "api/tasks/list/",
        views.CeleryTaskList.as_view(),
        name="api-tasks-list",
    ),
    path("api/tasks/retry/<str:task_id>", views.retry_task, name="api-retry-task"),
    path(
        "api/tasks/archive/",
        views.ArchiveTask.as_view(),
        name="api-tasks-archive",
    ),
    path(
        "api/tasks/cancel/",
        views.CancelTask.as_view(),
        name="api-tasks-cancel",
    ),
    path(
        "api/tasks/delete/",
        views.DeleteTask.as_view(),
        name="api-tasks-delete",
    ),
    path(
        "api/tasks/<str:task_id>/",
        views.CeleryTaskDetails.as_view(),
        name="api-tasks-details",
    ),
    path(
        "api/tasks/<str:task_id>/<log:log_file>/",
        views.CeleryTaskLogDetails.as_view(),
        name="api-tasks-log-details",
    ),
    path("account/", views.user_account, name="user-account"),
    path("update-account/", views.update_account, name="update-account"),
    path("update-preferences/", views.update_preferences, name="update-preferences"),
]
