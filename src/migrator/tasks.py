# myapp/tasks.py
import shlex
import subprocess
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from celery import shared_task
from celery.app.control import Inspect
from celery.result import AsyncResult
from celery.exceptions import TimeoutError
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.utils import timezone
from django_celery_results.models import TaskResult

from migrator.models import CeleryTask
from pymap import celery_app

logger = get_task_logger("CeleryTask")

FProc = Dict[str, (str | int)]
RProc = Dict[str, Any]
CALL_SYSTEM_TYPE = Dict[str, (str | FProc)]


def should_terminate_task(task_id: str) -> bool:
    # Implement logic to check if the task should terminate
    # For example, check a value in the database or cache
    task = CeleryTask.objects.filter(task_id=task_id).first()
    if task:
        if task.terminated:
            return True
    return False


def get_running_tasks() -> Dict[str, Dict[object, object]]:
    inspector = Inspect(app=celery_app)
    all_tasks: Dict[str, Dict[object, object]] = {
        "active": {},
        "reserved": {},
        "scheduled": {},
    }

    # Check active tasks
    active_tasks = inspector.active()
    logger.debug(f"ACTIVE TASKS: {active_tasks}")
    if active_tasks:
        for worker, tasks in active_tasks.items():
            all_tasks["active"][worker] = [
                f"{task['name']} :: {task['id']}" for task in tasks
            ]

    # Check reserved tasks
    reserved_tasks = inspector.reserved()
    logger.debug(f"RESERVED TASKS: {reserved_tasks}")
    if reserved_tasks:
        for worker, tasks in reserved_tasks.items():
            all_tasks["reserved"][worker] = [
                f"{task['name']} :: {task['id']}" for task in tasks
            ]

    # Check scheduled tasks
    scheduled_tasks = inspector.scheduled()
    logger.debug(f"SCHEDULED TASKS: {scheduled_tasks}")
    if scheduled_tasks:
        for worker, tasks in scheduled_tasks.items():
            all_tasks["scheduled"][worker] = [
                f"{task['name']} :: {task['id']}" for task in tasks
            ]

    return all_tasks


@shared_task
def long_running_test_task(timeout: int = 100, wait_timer: int = 5) -> None:
    ltime = timeout
    while ltime > 0:
        time.sleep(wait_timer)
        ltime = ltime - wait_timer


@shared_task(bind=True)
def call_system(self, cmd_list: Optional[List[str]]) -> CALL_SYSTEM_TYPE:
    # cmd_list is not optional and should always be a list of strings
    # however this is a failsafe to avoid parsing invalid data
    # It also is Optional to avoid type errors on the next statement
    # Was implemented due to retry task since the stored data is a string
    # and we need to parse it back to python
    if not isinstance(cmd_list, list):
        logger.critical(f"Expected cmd_list to be a list, got {type(cmd_list)}")
        self.update_state(
            state="FAILURE",
            meta={
                "status": "FAILURE",
            },
        )
        return {"status": "FAILURE"}
    root_directory: str = settings.PYMAP_LOGDIR
    total_cmds: int = len(cmd_list)
    max_procs: int = 5
    finished_procs: Dict[str, (str | int)] = {}
    running_procs: RProc = {}
    task_id = self.request.id
    log_directory = Path(root_directory, task_id)

    for i, cmd in enumerate(cmd_list):
        cmd_list[i] = cmd.replace(
            f"--logdir={root_directory}",
            f"--logdir={log_directory}",
        )

    # Just to ensure if the task is the one creating the path
    if not log_directory.exists():
        log_directory.mkdir()
    # Moved the check to the task itself to verify for cases of overwritting contents,
    # this will be slow if the directory has a lot of contents
    if len(sorted(log_directory.rglob("*.*"))) > 0:
        logger.warning(
            "Directory: %s seems to already exist and isn't completely empty, we might be overwritting files",
            log_directory,
        )

    def check_running(procs: RProc) -> RProc:
        for key in list(procs):
            proc = procs[key]
            if isinstance(proc, subprocess.Popen):
                status = proc.poll()
                if status is None:
                    continue
                else:
                    logger.info("Marked for removal: %s", key)
                    finished_procs[key] = status
                    procs.pop(key, None)
        return procs

    def terminate_all(procs: RProc) -> None:
        for key in list(procs):
            proc = procs[key]
            if isinstance(proc, subprocess.Popen):
                logger.info(f"Terminating {proc.pid}")
                proc.terminate()

    for index, cmd in enumerate(cmd_list):
        logger.info("Task %s Scheduling %s", task_id, index)
        # Some complex passwords or our regex/custom logic might fail to create a viable
        # "command" string, in this case let shlex fail to avoid shell escapes
        try:
            shlex.split(cmd)
        except ValueError:
            logger.critical("Failed to parse and split the string received")
            # logger.debug(
            #     "Received the following command string: %s", cmd, exc_info=True
            # )
            # Continue to the next iteration of the loop
            continue
        n_cmd = subprocess.Popen(
            shlex.split(cmd),
            stdin=None,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
        running_procs[str(index)] = n_cmd
        while len(running_procs) >= max_procs:
            logger.info("%s Waiting for Queue", task_id)
            running_procs = check_running(running_procs)
            time.sleep(4)

        self.update_state(
            state="PROGRESS",
            meta={
                "processing": len(running_procs),
                "pending": len(cmd_list),
                "total": total_cmds,
                "return_codes": finished_procs,
                "status": "Processing...",
            },
        )
        if should_terminate_task(task_id):
            terminate_all(running_procs)

    while running_procs:
        running_procs = check_running(running_procs)
        nrp = len(running_procs)
        if should_terminate_task(task_id):
            terminate_all(running_procs)
        self.update_state(
            state="PROGRESS",
            meta={
                "processing": nrp,
                "pending": nrp,
                "total": total_cmds,
                "return_codes": finished_procs,
                "status": "Processing...",
            },
        )
        time.sleep(10)

    self.update_state(
        state="SUCCESS",
        meta={
            "processing": 0,
            "pending": 0,
            "total": total_cmds,
            "return_codes": finished_procs,
            "status": "SUCCESS",
        },
    )

    logger.info("Finished Task: %s , calculating run time...", task_id)
    ctask = CeleryTask.objects.get(task_id=task_id)

    # Calculate run time in seconds
    # TODO: Investigate celery's builtin runtime calculation
    # https://stackoverflow.com/questions/33860242/extract-runtime-and-time-of-completion-from-celery-task

    start_time = ctask.start_time
    end_time = timezone.now()
    run_time_seconds = int((end_time - start_time).total_seconds())

    logger.debug("START TIME: %s", ctask.start_time)
    logger.debug("RUN TIME: %s", run_time_seconds)

    # Update the run_time field in the database
    ctask.run_time = run_time_seconds
    # Make sure to mark the task as finished
    # We can probably hook onto task's failure/success status and mark the task
    # as finished there to avoid tasks never being finished when they crash
    ctask.finished = True
    ctask.save()

    return {"status": "SUCCESS", "return_codes": finished_procs}


# I'm not sure how the django admin scheduler passes the arguments, assuming as string
@shared_task
def purge_results(
    days: int = int("1"),
    hours: int = int("0"),
    minutes: int = int("0"),
    finished_field: str = "true",
) -> None:
    td = timedelta(days=1, hours=0, minutes=0)
    try:
        td = timedelta(days=days, hours=hours, minutes=minutes)
    except ValueError:
        logger.error(
            "Invalid values passed to purge results: Days %s, Hours %s, Minutes %s",
            days,
            hours,
            minutes,
        )
    # Calculate the cutoff date
    finished = False if finished_field == "false" else True
    logger.debug(
        f"""
                 Values received from administration:
                    Days: {days},
                    Hours: {hours},
                    Minutes: {minutes},
                    finished_field<type>: {finished_field}<{type(finished_field)}]>,
                    finished: {finished},
                 """
    )
    cutoff_date = datetime.now() - td
    logger.info("Starting purge of results older than: %s", td)

    # Filter the queryset to get tasks older than the cutoff date
    # Avoid Purging results from running tasks, don't purge results from tasks that have already been purged
    tasks = CeleryTask.objects.filter(
        start_time__lt=cutoff_date, finished=finished, results_purged=False
    )
    logger.info("We will try to purge %s results", len(tasks))

    for task in tasks:
        purged = True
        try:
            result = AsyncResult(task.task_id, app=celery_app)
            result.get(timeout=5.0)
            result.forget()
        except TimeoutError:
            logger.error("Failed to clear results for Task ID<%s>", task.task_id)
        try:
            result = TaskResult.objects.get(task_id=task.task_id)
            logger.debug("Purging result for Task ID<%s> from database", task.task_id)
            result.delete()
        except ObjectDoesNotExist:
            logger.info(
                "We don't seem to have any results associated with: %s",
                task.task_id,
            )
        except ImproperlyConfigured:
            # If TaskResult model is not available, log or handle the situation
            logger.warning("Task results backend is not configured to use django-db.")
        except Exception as e:
            logger.critical("Unhandled exception %s", e, exc_info=True)
            purged = False
        if purged:
            task.results_purged = True
            task.save()


# Some tasks where not being set as finished, can also be run periodically
# for tasks that may have crashed
@shared_task
def validate_finished() -> None:
    FINISHED_STATES = ["FAILURE", "SUCCESS"]

    def _task_exists(task_id: str) -> bool:
        inspector = Inspect(app=celery_app)

        # Check active tasks
        active_tasks = inspector.active()
        logger.debug(f"ACTIVE TASKS: {active_tasks}")
        if active_tasks:
            for _, tasks in active_tasks.items():
                for task in tasks:
                    if task["id"] == task_id:
                        return True

        # Check reserved tasks
        reserved_tasks = inspector.reserved()
        logger.debug(f"RESERVED TASKS: {active_tasks}")
        if reserved_tasks:
            for _, tasks in reserved_tasks.items():
                for task in tasks:
                    if task["id"] == task_id:
                        return True

        # Check scheduled tasks
        scheduled_tasks = inspector.scheduled()
        logger.debug(f"SCHEDULED TASKS: {active_tasks}")
        if scheduled_tasks:
            for _, tasks in scheduled_tasks.items():
                for task in tasks:
                    if task["request"]["id"] == task_id:
                        return True

        # Task not found
        return False

    def _is_finished(task: CeleryTask) -> bool:
        async_result = AsyncResult(task.task_id, app=celery_app)
        # The results have already been purged we can't check task state
        # Let's hope no one purges results in running tasks
        if task.results_purged:
            logger.debug("Task's results where purged from database")
            return True
        # Check status to ensure task is not running:
        # https://docs.celeryq.dev/en/latest/reference/celery.result.html#celery.result.AsyncResult.status
        elif async_result.status in FINISHED_STATES:
            logger.debug("Task status is either FAILURE OR SUCCESS")
            return True
        elif async_result.ready():
            logger.debug("Task responded as ready")
            return True
        # If the database is being used and results have not been purged
        # then AsyncResult should return status, however just to be extra safe
        elif settings.CELERY_RESULT_BACKEND == "django-db":
            try:
                task_result = TaskResult.objects.get(task_id=task.task_id)
                logger.debug(
                    "Found result in database: %s, STATUS:%s",
                    task_result,
                    task_result.status,
                )
                if task_result.status in FINISHED_STATES:
                    return True
            except ObjectDoesNotExist:
                logger.info(
                    "This result does not exist in the database: %s", task.task_id
                )
        # We need to handle the fact that the result might have been manually deleted
        # however the task crashed and was still not set as finished
        # Status can be PENDING for unkown/deleted tasks
        elif async_result.status == "PENDING":
            try:
                return _task_exists(task.task_id)
            except AttributeError:
                logger.error(
                    "We are trying to access task ID in queues, but the response structure seems to have changed"
                )
        return False

    logger.info("Checking for non running unfinished tasks")
    unfinished = CeleryTask.objects.filter(finished=False)
    if not unfinished.exists():
        # No tasks marked as unfinished exit earlier
        logger.info("No tasks in an unfinished state")
        return
    for task in unfinished:
        logger.debug("Checking task %s", task.task_id)
        finished = _is_finished(task)
        if finished:
            logger.info("Setting task %s as finished", task.task_id)
            task.finished = True
            task.save()


# This will be used to automate the archival of tasks by a certain date,
# It should not be pre-configured and the admin must create a periodic task
@shared_task
def archive_older_than(
    weeks: int = int("4"),
    days: int = int("0"),
    hours: int = int("0"),
    minutes: int = int("0"),
) -> None:
    td = timedelta(weeks=4, days=0, hours=0, minutes=0)
    try:
        td = timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes)
    except ValueError:
        logger.error(
            "Invalid values passed to archive older tasks: Days %s, Hours %s, Minutes %s",
            days,
            hours,
            minutes,
        )
        # Here we actually don't continue we might not want to archive by the default values
        return
    cutoff_date = datetime.now() - td
    tasks = CeleryTask.objects.filter(start_time__lt=cutoff_date, finished=True)
    tasks.update(archived=True)
