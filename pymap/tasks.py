import logging
from celery import shared_task
from django.core.cache import cache
from imapsync_scriptgen.generator import generate, ImapSyncSpec
from .models import MigrationTask

logger = logging.getLogger("pymap.tasks")


@shared_task
def run_imap_sync(task_id: str, host1: str, host2: str, extra_args: str):
    """
    Execute imap sync for a single migration task.

    Credentials are fetched from Redis cache at runtime.
    Never receives plaintext passwords in Celery arguments.
    """
    try:
        task = MigrationTask.objects.get(id=task_id)
    except MigrationTask.DoesNotExist:
        logger.error("Task %s not found", task_id)
        return

    # Fetch credentials from cache (stored during job submission)
    secrets = cache.get(f"imap_secret:{task.credential_ref}")
    if not secrets:
        logger.error("Task %s: credentials expired or not found", task_id)
        task.status = "FAILED"
        task.save()
        return

    task.status = "RUNNING"
    task.save()

    # Build ImapSyncSpec for the imapsync-scriptgen library
    spec = ImapSyncSpec(
        host1=host1,
        user1=task.user1,
        pass1_ref="pw1",
        host2=host2,
        user2=task.user2,
        pass2_ref="pw2",
        logfile=task.logfile,
        extra_args=extra_args or None,
        logdir="/var/log/ARKA_LOGS",  # Configured log directory
    )

    try:
        # Call imapsync-scriptgen generate() with runtime secrets
        # This builds the actual imapsync command with passwords substituted
        cmd = generate(
            spec, runtime_secrets={"pw1": secrets["pass1"], "pw2": secrets["pass2"]}
        )

        # TODO: Execute the actual imapsync command here
        # subprocess.run(cmd.argv, check=True)
        # For now, just log the redacted command
        logger.info("Task %s: %s", task_id, str(cmd))

        # Mark task as successful
        task.status = "SUCCESS"

    except Exception as e:
        logger.exception("Task %s failed: %s", task_id, str(e))
        task.status = "FAILED"
    finally:
        task.save()
