from typing import Any
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Adds an administrator for the app in case no users exist"

    def handle(self, *args: object, **options: Any) -> None:
        if User.objects.count() > 0:
            raise CommandError(
                "Cannot instantiate admin when there are already users present in the database"
            )
        username = "pymin"
        email = "pymap@localhost"
        password = "CHANGEME!"
        admin = User.objects.create_superuser(
            email=email, username=username, password=password
        )
        admin.is_active = True
        admin.is_superuser = True
        admin.save()
        self.stdout.write(
            self.style.SUCCESS("Created account for %s (%s)" % (username, email))
        )
