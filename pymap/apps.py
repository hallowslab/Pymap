from django.db.models import Sum
from django.apps import AppConfig
from django.utils.safestring import mark_safe


class PymapConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pymap"
    verbose_name = "Pymap"
    is_modular = True
    root_url = "/PYMAP"
    icon = mark_safe(
        '<img src="/static/pymap/pymap_sq.png" alt="Pymap" style="height:1.2em; vertical-align:middle;">'
    )

    def get_dashboard_stats(self):
        from .models import MigrationJob, MigrationTask

        total_jobs = MigrationJob.objects.count()
        success_jobs = MigrationJob.objects.filter(status="SUCCESS").count()
        failed_jobs = MigrationJob.objects.filter(status="FAILED").count()

        job_success_pct = (success_jobs / total_jobs * 100) if total_jobs > 0 else 0
        job_failed_pct = (failed_jobs / total_jobs * 100) if total_jobs > 0 else 0

        total_tasks = MigrationTask.objects.count()
        success_tasks = MigrationTask.objects.filter(status="SUCCESS").count()
        failed_tasks = MigrationTask.objects.filter(status="FAILED").count()
        total_task_runtime_seconds = (
            MigrationTask.objects.aggregate(total=Sum("run_time"))["total"] or 0
        )
        total_task_runtime_hours = total_task_runtime_seconds / 3600

        task_success_pct = (success_tasks / total_tasks * 100) if total_tasks > 0 else 0
        task_failed_pct = (failed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return {
            "Total Jobs": total_jobs,
            "Job Success Rate": f"{job_success_pct:.1f}%",
            "Job Failure Rate": f"{job_failed_pct:.1f}%",
            "Total Tasks": total_tasks,
            "Task Success Rate": f"{task_success_pct:.1f}%",
            "Task Failure Rate": f"{task_failed_pct:.1f}%",
            "Total Task Runtime (Hours)": f"{total_task_runtime_hours:.1f}",
        }

    def get_worker_metrics(self):
        return {
            "(WIP)Running Jobs": "Unknown",
            "(WIP)Queued Jobs": "Unknown",
            "(WIP)Average Runtime": "Unknown",
            "(WIP)Success Rate": "Unknown",
        }
