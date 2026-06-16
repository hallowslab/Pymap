import logging
import subprocess
import time
import os
import signal
import socket
from django.utils import timezone
from django.conf import settings
from celery import shared_task
from django.core.cache import cache

try:
    from imapsync_scriptgen.generator import generate, ImapSyncSpec
except ImportError:
    generate = None
    ImapSyncSpec = None
from .models import MigrationTask, MigrationJob
from .utils import build_logfile

logger = logging.getLogger("pymap.tasks")


def _finish_task(
    task: MigrationTask, status: str, exit_code: int | None = None
) -> None:
    task.status = status
    if exit_code is not None:
        task.exit_code = exit_code
    task.end_time = timezone.now()
    # Model uses auto_now_add on task.start_time
    if task.start_time:
        task.run_time = max(int((task.end_time - task.start_time).total_seconds()), 0)
    task.save()


@shared_task(bind=True)
def run_imap_sync(self, task_id: str, host1: str, host2: str, extra_args: str):
    """
    Execute imap sync for a single migration task.

    Credentials are fetched from Redis cache at runtime.
    Never receives plaintext passwords in Celery arguments.
    """
    task = None
    job = None
    try:
        try:
            task = MigrationTask.objects.get(id=task_id)
            job = task.job
        except MigrationTask.DoesNotExist:
            logger.error("Task %s not found", task_id)
            return

        # Check if task was already revoked before starting
        # Note: self.AsyncResult requires a result backend to be configured
        if task.terminated:
            logger.warning("Task %s: User terminated before start", task_id)
            _finish_task(task, "FAILED")
            return

        # Fetch credentials from cache (stored during job submission)
        secrets = cache.get(f"imap_secret:{task.credential_ref}")
        if not secrets:
            logger.error("Task %s: credentials expired or not found", task_id)
            _finish_task(task, "FAILED")
            return

        # Ensure Task logfile path has ARKA_LOGDIR and job.id
        job_log_dir = os.path.join(settings.ARKA_LOGDIR, "pymap", str(job.id))
        if not os.path.exists(job_log_dir):
            os.makedirs(job_log_dir, exist_ok=True)

        # Use the stored logfile name from the task model
        logfile = task.logfile
        if not logfile:
            logfile = build_logfile(job, task)
            task.logfile = logfile
            task.save(update_fields=["logfile"])

        task.status = "RUNNING"
        task.save()

        # Update job status to RUNNING if it's still PENDING
        MigrationJob.objects.filter(id=job.id, status="PENDING").update(
            status="RUNNING"
        )

        if not generate or not ImapSyncSpec:
            logger.error("Task %s: imapsync_scriptgen is not installed", task_id)
            _finish_task(task, "FAILED")
            return

        # Build ImapSyncSpec for the imapsync-scriptgen library
        spec = ImapSyncSpec(
            host1=host1,
            user1=task.user1,
            pass1_ref="pw1",
            host2=host2,
            user2=task.user2,
            pass2_ref="pw2",
            logfile=logfile,
            extra_args=extra_args or None,
            logdir=job_log_dir,
        )

        # Call imapsync-scriptgen generate() with runtime secrets
        # This builds the actual imapsync command with passwords substituted
        cmd = generate(
            spec, runtime_secrets={"pw1": secrets["pass1"], "pw2": secrets["pass2"]}
        )

        logger.info("Task %s: Starting imapsync", task_id)

        # logger.debug("Generated command: %s", getattr(cmd, "argv", None))
        # Execute the imapsync command
        # No need to manually redirect logs as imapsync handles it via --logfile
        try:
            process = subprocess.Popen(
                cmd.argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
        except Exception as e:
            logger.exception("Failed to start subprocess: %s", e)
            _finish_task(task, "FAILED")
            return

        # Store PID and hostname
        task.pid = process.pid
        task.worker_hostname = socket.gethostname()
        task.save()

        # Polling loop for termination and completion
        while process.poll() is None:
            task.refresh_from_db(fields=["terminated"])
            if task.terminated:
                logger.warning(
                    "Task %s: Revocation detected. Escalating termination for process %d",
                    task_id,
                    process.pid,
                )

                # SIGTERM first
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)

                # Wait for up to 30s
                for _ in range(30):
                    if process.poll() is not None:
                        break
                    time.sleep(1)

                # If still alive, SIGKILL
                if process.poll() is None:
                    logger.error(
                        "Task %s: Process %d didn't stop with SIGTERM. Sending SIGKILL.",
                        task_id,
                        process.pid,
                    )
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)

                exit_code = process.returncode if process.poll() is not None else None
                _finish_task(task, "FAILED", exit_code=exit_code)
                job.update_status()
                return

            logger.debug(f"Polling Task ID {task_id}")
            # Wait before next poll
            time.sleep(5)

        exit_code = process.returncode
        if exit_code == 0:
            logger.info("Task %s: imapsync completed successfully", task_id)
            finish_status = "SUCCESS"
        else:
            logger.error(
                "Task %s: imapsync failed with exit code %d",
                task_id,
                exit_code,
            )
            finish_status = "FAILED"

        _finish_task(task, finish_status, exit_code=exit_code)
        job.update_status()

    except Exception as e:
        logger.exception("Task %s failed: %s", task_id, str(e))
        if task:
            _finish_task(task, "FAILED")
            if job:
                job.update_status()
