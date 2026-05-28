from django.urls import path
from . import views

app_name = "pymap"

urlpatterns = [
    path("", views.job_list, name="job-list"),
    path("jobs/create/", views.submit_job, name="job-create"),
    path("jobs/<uuid:job_id>/", views.job_detail, name="job-detail"),
    path(
        "tasks/<uuid:task_id>/terminate/", views.terminate_task, name="terminate-task"
    ),
    path("tasks/<uuid:task_id>/log/", views.view_task_log, name="task-log"),
    path(
        "tasks/<uuid:task_id>/log/download/",
        views.download_task_log,
        name="task-log-download",
    ),
]
