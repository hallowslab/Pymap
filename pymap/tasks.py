import logging
from celery import shared_task
from django.core.cache import cache
from imapsync_scriptgen.generator import generate, ImapSyncSpec
from .models import MigrationTask

logger = logging.getLogger("pymap.tasks")


@shared_task
def run_imap_sync(task_id: str, host1: str, host2: str, extra_args: str):
    task = MigrationTask.objects.get(id=task_id)
    secrets = cache.get(f"imap_secret:{task.credential_ref}")
    if not secrets:
        task.status = "FAILED"
        task.save()
        return

    task.status = "RUNNING"
    task.save()

    spec = ImapSyncSpec(
        host1=host1,
        user1=task.user1,
        pass1_ref="pw1",
        host2=host2,
        user2=task.user2,
        pass2_ref="pw2",
        logfile=task.logfile,
        extra_args=extra_args,
        logdir="/tmp",  # adjust as needed
    )

    try:
        cmd = generate(
            spec, runtime_secrets={"pw1": secrets["user1"], "pw2": secrets["user2"]}
        )
        logger.info("Task %s: %s", task_id, " ".join(cmd.redacted_argv))
        task.status = "SUCCESS"
    except Exception as e:
        logger.exception("Task %s failed", task_id)
        task.status = "FAILED"
    finally:
        task.save()
