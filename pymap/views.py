import uuid
from collections import deque
from django.shortcuts import render, get_object_or_404, redirect
from django.core.cache import cache
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from pathlib import Path
from django.http import (
    FileResponse,
    HttpResponse,
    HttpResponseRedirect,
    HttpRequest,
    Http404,
)
from django.contrib import messages

from .models import MigrationTask, MigrationJob
from .tasks import run_imap_sync
from .utils import build_logfile


@login_required
def job_list(request: HttpRequest) -> HttpResponse:
    """List migration jobs, filtered by user and search terms, newest first."""
    jobs = MigrationJob.objects.all()

    if not request.user.is_superuser:
        jobs = jobs.filter(owner=request.user)

    source = request.GET.get("source", "").strip()
    dest = request.GET.get("dest", "").strip()
    custom_id = request.GET.get("custom_id", "").strip()

    if source:
        jobs = jobs.filter(source_host__icontains=source)
    if dest:
        jobs = jobs.filter(dest_host__icontains=dest)
    if custom_id:
        jobs = jobs.filter(custom_identifier__icontains=custom_id)

    jobs = jobs.order_by("-created_at")

    page_number = request.GET["page"] if "page" in request.GET else 1
    paginator = Paginator(jobs, 10)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "pymap/jobs_list.html",
        {
            "items": page_obj.object_list,
            "columns": [
                "ID",
                "Custom Identifier",
                "Source",
                "Destination",
                "Tasks",
                "Status",
                "Created",
            ],
            "row_template": "pymap/rows/job_row.html",
            "empty_message": "No jobs yet.",
            "page_obj": page_obj,
            "pagination": {
                "page": page_obj.number,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
            },
            "search_enabled": True,
            "search_fields": [
                {
                    "name": "source",
                    "placeholder": "Source",
                    "value": source,
                },
                {
                    "name": "dest",
                    "placeholder": "Destination",
                    "value": dest,
                },
                {
                    "name": "custom_id",
                    "placeholder": "Custom Identifier",
                    "value": custom_id,
                },
            ],
        },
    )


@login_required
def job_detail(request: HttpRequest, job_id) -> HttpResponse:
    """Show job info and all associated tasks."""
    job = get_object_or_404(MigrationJob, id=job_id)
    if job.owner != request.user and not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this job.")
        return redirect("pymap:job-list")
    tasks = job.tasks.all()

    page_number = request.GET["page"] if "page" in request.GET else 1
    paginator = Paginator(tasks, 10)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "pymap/job_detail.html",
        {
            "job": job,
            "items": page_obj.object_list,
            "columns": [
                "ID",
                "Source User",
                "Destination User",
                "Domains",
                "Status",
                "Log File",
                "Actions",
            ],
            "row_template": "pymap/rows/task_row.html",
            "empty_message": "No tasks for this job.",
            "page_obj": page_obj,
            "pagination": {
                "page": page_obj.number,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
            },
            "search_enabled": False,
        },
    )


@login_required
def submit_job(request: HttpRequest) -> HttpResponse | HttpResponseRedirect:
    """
    Form for creating a new migration job.

    Credentials format (one per line):
        user1@domain.com password1
        user1@domain.com password1 user2@domain.com password2

    If only one user/password is provided, it's used for both source and destination.
    """
    assert isinstance(request.user, User)
    if request.method == "POST":
        source_host = request.POST.get("source_host", "").strip()
        dest_host = request.POST.get("dest_host", "").strip()
        additional_args = request.POST.get("additional_args", "").strip()
        custom_identifier = request.POST.get("custom_identifier", "").strip()
        credentials_text = request.POST.get("credentials", "")
        user = request.user

        # Validate required fields
        if not source_host or not dest_host:
            messages.error(request, "Source and destination hosts are required.")
            return render(request, "pymap/job_create.html")

        if not credentials_text.strip():
            messages.error(request, "At least one credential line is required.")
            return render(request, "pymap/job_create.html")

        job = MigrationJob.objects.create(
            source_host=source_host,
            dest_host=dest_host,
            additional_args=additional_args or None,
            custom_identifier=custom_identifier or None,
            owner=user,
        )

        # Parse credential lines and create tasks
        valid_tasks_count = 0
        invalid_lines = []

        for line_num, line in enumerate(credentials_text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 2:
                invalid_lines.append(
                    f"Line {line_num}: insufficient data (need at least user and password)"
                )
                continue

            # Parse credentials: user1 pass1 [user2 pass2]
            user1, pass1 = parts[0], parts[1]
            if len(parts) >= 4:
                user2, pass2 = parts[2], parts[3]
            else:
                # Same credentials for source and destination
                user2, pass2 = user1, pass1

            # Store credentials in Redis cache with TTL (1 hour)
            # Never pass plaintext passwords in Celery arguments
            credential_ref = str(uuid.uuid4())
            cache.set(
                f"imap_secret:{credential_ref}",
                {"pass1": pass1, "pass2": pass2},
                timeout=3600,
            )

            task = MigrationTask.objects.create(
                job=job,
                user1=user1,
                user2=user2,
                credential_ref=credential_ref,
                logfile=build_logfile(job, user1=user1, user2=user2),
            )

            # Launch Celery task - set Celery task ID to match MigrationTask.id for easy revocation
            run_imap_sync.apply_async(
                args=[str(task.id), source_host, dest_host, additional_args or ""],
                task_id=str(task.id),
            )
            valid_tasks_count += 1

        # Provide feedback
        if valid_tasks_count > 0:
            messages.success(request, f"Job created with {valid_tasks_count} task(s).")

        if invalid_lines:
            messages.warning(
                request,
                f"Skipped {len(invalid_lines)} invalid line(s): {'; '.join(invalid_lines)}",
            )

        return redirect("pymap:job-detail", job_id=job.id)

    return render(request, "pymap/job_create.html")


@login_required
def terminate_task(request: HttpRequest, task_id) -> HttpResponseRedirect:
    """Mark a migration task as terminated."""
    task = get_object_or_404(MigrationTask, id=task_id)
    # Check permissions (only owner or superuser)
    if task.job.owner != request.user and not request.user.is_superuser:
        messages.error(request, "You do not have permission to terminate this task.")
        return redirect("pymap:job-detail", job_id=task.job.id)

    if task.status == "RUNNING":
        task.terminated = True
        task.save()
        messages.success(request, f"Task for {task.user1} termination requested.")
    else:
        messages.warning(request, f"Task for {task.user1} is not running.")

    return redirect("pymap:job-detail", job_id=task.job.id)


DEFAULT_TASK_LOG_LINES = 50


@login_required
def view_task_log(request: HttpRequest, task_id) -> HttpResponse:
    """View the logfile contents of a single task."""
    task = get_object_or_404(MigrationTask, id=task_id)

    log_content = ""
    if "lines" not in request.GET:
        line_limit = str(DEFAULT_TASK_LOG_LINES)
    else:
        line_limit = request.GET.get("lines", "").strip()

    task_log_path = task.log_path
    if task_log_path and Path(task_log_path).exists():
        try:
            if line_limit:
                try:
                    lines_count = int(line_limit)
                    if lines_count > 0:
                        with open(task_log_path, "r", encoding="utf-8") as f:
                            log_content = "".join(deque(f, maxlen=lines_count))
                    else:
                        line_limit = ""
                except ValueError:
                    line_limit = ""
            if not line_limit:
                with open(task_log_path, "r", encoding="utf-8") as f:
                    log_content = f.read()
        except Exception as e:
            log_content = f"Error reading log file: {str(e)}"
    else:
        log_content = f"Log file not found at {task_log_path}. It may not have been created yet or has been deleted."

    return render(
        request,
        "pymap/task_log.html",
        {"task": task, "log_content": log_content, "line_limit": line_limit},
    )


@login_required
def download_task_log(request: HttpRequest, task_id) -> FileResponse:
    """Download the logfile for a single task."""
    task = get_object_or_404(MigrationTask, id=task_id)
    if task.job.owner != request.user and not request.user.is_superuser:
        messages.error(request, "You do not have permission to download this log.")
        raise Http404

    task_log_path = task.log_path
    if not task_log_path or not Path(task_log_path).exists():
        raise Http404

    return FileResponse(
        open(task_log_path, "rb"),
        as_attachment=True,
        filename=Path(task_log_path).name,
    )
