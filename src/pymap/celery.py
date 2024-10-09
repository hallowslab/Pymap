import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pymap.settings")

app = Celery("pymap")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


def get_worker_queues():
    inspector = app.control.inspect()
    active_queues = inspector.active_queues()

    queues = {}
    if active_queues:
        for worker, queues_list in active_queues.items():
            queues[worker] = [queue["name"] for queue in queues_list]

    return queues


@app.task(bind=True, ignore_result=True)
def debug_task(self) -> None:
    print(f"Request: {self.request!r}")
