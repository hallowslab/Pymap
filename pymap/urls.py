from django.urls import path
from . import views

app_name = "pymap"

urlpatterns = [
    path("", views.index, name="pymap_home"),
    path("jobs/", views.job_list, name="job-list"),
    path("jobs/create/", views.submit_job, name="job-create"),
    path("jobs/<uuid:job_id>/", views.job_detail, name="job-detail"),
]
