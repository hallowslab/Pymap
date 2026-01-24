from django.urls import path
from . import views

app_name = "pymap"

urlpatterns = [
    path("", views.index, name="pymap_home"),
    path("jobs/", views.job_list, name="job_list"),
    path("submit/", views.submit_job, name="submit_job"),
    path("job/<uuid:job_id>/", views.job_detail, name="job_detail"),
]
