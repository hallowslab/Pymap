# myapp/tasks.py
import shlex
import subprocess
import time
from typing import List, Dict, Any
from os import mkdir
from os.path import isdir

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone

from migrator.models import CeleryTask

logger = get_task_logger("CeleryTask")

FProc = Dict[str, (str | int)]
RProc = Dict[str, Any]


@shared_task(bind=True)
def call_system(self, cmd_list: List[str]) -> Dict[str, (str | FProc)]:
    root_directory: str = settings.PYMAP_SETTINGS.get("LOGDIR", "/var/log/pymap")
    total_cmds: int = len(cmd_list)
    max_procs: int = 4
    finished_procs: Dict[str, (str | int)] = {}
    running_procs: RProc = {}
    task_id = self.request.id
    log_directory = f"{root_directory}/{task_id}"

    for i, cmd in enumerate(cmd_list):
        cmd_list[i] = cmd.replace(
            f"--logdir={root_directory}",
            f"--logdir={log_directory}",
        )

    # Moved the check to the task itself to verify for cases of overwritting contents,
    # here none of the commands have been executed so even if they create the directory
    # it should not exist yet
    if not isdir(log_directory):
        mkdir(log_directory)
    else:
        logger.warning(
            "Directory: %s seems to already exist, we might be writting over files",
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

    for index, cmd in enumerate(cmd_list):
        logger.info("Task %s Scheduling %s", task_id, index)
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

    while running_procs:
        running_procs = check_running(running_procs)
        nrp = len(running_procs)
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
        time.sleep(4)

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
    ctask.save()

    return {"status": "Executed all commands", "return_codes": finished_procs}
