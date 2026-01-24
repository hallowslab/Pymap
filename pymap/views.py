import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.core.cache import cache
from django.contrib import messages

from .models import MigrationJob, MigrationTask
from .tasks import run_imap_sync


def index(request):
    """PYMAP home page."""
    return render(request, "pymap/pymap_index.html")


def job_list(request):
    """List all migration jobs, newest first."""
    jobs = MigrationJob.objects.all().order_by("-created_at")
    return render(request, "pymap/jobs_list.html", {"jobs": jobs})


def job_detail(request, job_id):
    """Show job info and all associated tasks."""
    job = get_object_or_404(MigrationJob, id=job_id)
    tasks = job.tasks.all()
    return render(request, "pymap/job_detail.html", {"job": job, "tasks": tasks})


def submit_job(request):
    """
    Form for creating a new migration job.

    Credentials format (one per line):
        user1@domain.com password1
        user1@domain.com password1 user2@domain.com password2

    If only one user/password is provided, it's used for both source and destination.
    """
    if request.method == "POST":
        source_host = request.POST.get("source_host", "").strip()
        dest_host = request.POST.get("dest_host", "").strip()
        additional_args = request.POST.get("additional_args", "").strip()
        credentials_text = request.POST.get("credentials", "")

        # Validate required fields
        if not source_host or not dest_host:
            messages.error(request, "Source and destination hosts are required.")
            return render(request, "pymap/job_create.html")

        if not credentials_text.strip():
            messages.error(request, "At least one credential line is required.")
            return render(request, "pymap/job_create.html")

        # Create the job
        job = MigrationJob.objects.create(
            source_host=source_host,
            dest_host=dest_host,
            additional_args=additional_args or None,
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

            # Create the migration task
            task = MigrationTask.objects.create(
                job=job,
                user1=user1,
                user2=user2,
                credential_ref=credential_ref,
                logfile=f"{job.id}_{user1}.log",
            )

            # Launch Celery task - only pass task.id and credential_ref (no plaintext)
            run_imap_sync.delay(
                str(task.id), source_host, dest_host, additional_args or ""
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
