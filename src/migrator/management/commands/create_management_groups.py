from typing import Any
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from migrator.models import CeleryTask

from django.db.models import Model

from django_celery_results.models import TaskResult


class Command(BaseCommand):
    help = "Adds a group for managing the users trough the admin dashboard"

    def manage_group(
        self, group_name: str, model: type[Model], group_permissions: list[str]
    ) -> None:
        def has_permission(group: Group, perm: Permission) -> bool:
            return group.permissions.filter(codename=perm.codename).exists()

        # Get or create the group
        group, _ = Group.objects.get_or_create(name=group_name)

        # Get the permissions related to the User model
        model_content_type = ContentType.objects.get_for_model(model)
        permissions = Permission.objects.filter(content_type=model_content_type).filter(
            codename__in=group_permissions
        )

        # Add permissions to the group
        for perm in permissions:
            if not has_permission(group, perm):
                self.stdout.write(
                    self.style.SUCCESS(f"Adding {perm.codename} to {group_name}")
                )
                group.permissions.add(perm)
            else:
                self.stdout.write(
                    self.style.WARNING(f"{group_name} already has {perm.codename}")
                )

        # Save the group
        group.save()

    def handle(self, *args: object, **options: Any) -> None:
        # Create User Managers group
        self.manage_group(
            "User Managers",
            User,
            ["add_user", "change_user", "delete_user", "view_user"],
        )
        # Create Task Managers group
        self.manage_group(
            "Task Managers", TaskResult, ["view_taskresult", "delete_taskresult"]
        )
        self.manage_group(
            "Task Managers",
            CeleryTask,
            ["view_celerytask", "delete_celerytask", "change_celerytask"],
        )
