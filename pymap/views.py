from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from .models import MigrationJob, MigrationTask

# Create your views here.


def index(request):
    return render(request, "pymap_index.html")


def job_detail(request, job_id):
    job = get_object_or_404(MigrationJob, id=job_id)
    tasks = job.tasks.all()
    return render(request, "job_detail.html", {"job": job, "tasks": tasks})


def job_list(request):
    jobs = MigrationJob.objects.all().order_by("-created_at")

    return render(request, "job_list.html", {"jobs": jobs})


def submit_job(request):
    if request.method == "POST":
        source_host = request.POST["source_host"]
        dest_host = request.POST["dest_host"]
        additional_args = request.POST.get("additional_args", "")
        credentials_text = request.POST["credentials"]  # multiline input

        job = MigrationJob.objects.create(
            source_host=source_host,
            dest_host=dest_host,
            additional_args=additional_args,
        )

        for line in credentials_text.splitlines():
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 2:
                continue  # skip invalid lines

            user1, pass1 = parts[0], parts[1]
            if len(parts) >= 4:
                user2, pass2 = parts[2], parts[3]
            else:
                user2, pass2 = user1, pass1

            credential_ref = str(uuid.uuid4())
            cache.set(
                f"imap_secret:{credential_ref}",
                {"user1": pass1, "user2": pass2},
                timeout=3600,
            )

            task = MigrationTask.objects.create(
                job=job,
                user1=user1,
                user2=user2,
                credential_ref=credential_ref,
                logfile=f"{job.id}_{user1}.log",
            )

            run_imap_sync.delay(str(task.id), source_host, dest_host, additional_args)

        return redirect("job_detail", job_id=job.id)

    return render(request, "submit_job.html")
