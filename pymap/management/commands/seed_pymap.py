from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pymap.models import MigrationJob, MigrationTask
import random
import uuid
import secrets


class Command(BaseCommand):
    help = "Seed database with dummy Pymap jobs and tasks"

    def handle(self, *args, **kwargs):
        USERNAME = "PymapTest"
        EMAIL = "pymaptest@arka.internal"
        # Create user
        user, created = User.objects.get_or_create(
            username=USERNAME,
            defaults={
                "email": EMAIL,
                "is_superuser": False,
                "is_staff": False,
            },
        )
        if created:
            user.set_password(secrets.token_urlsafe(32))
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created {USERNAME} user"))
        else:
            self.stdout.write(self.style.WARNING(f"{USERNAME} user already exists"))

        statuses = ["PENDING", "RUNNING", "SUCCESS", "FAILED", "CHECK"]

        for i in range(10):
            job = MigrationJob.objects.create(
                owner=user,
                source_host=f"imap.arkasrc{i}.internal",
                dest_host=f"imap.arkadst{i}.internal",
                custom_identifier=f"Test Job {i}",
                status=random.choice(statuses),
            )

            # Create 1-3 tasks per job
            num_tasks = random.randint(1, 3)
            for j in range(num_tasks):
                # If job is pending/running, task should be too. Otherwise success/failed.
                if job.status in ["PENDING", "RUNNING"]:
                    task_status = job.status
                else:
                    task_status = random.choice(["SUCCESS", "FAILED"])

                MigrationTask.objects.create(
                    job=job,
                    user1=f"user{j}@source{i}.com",
                    user2=f"user{j}@dest{i}.com",
                    credential_ref=str(uuid.uuid4()),
                    run_time=random.randint(1, 3600),
                    status=task_status,
                    logfile=f"{job.id}_user{j}.log",
                )

        self.stdout.write(self.style.SUCCESS("Successfully seeded 10 jobs with tasks"))
