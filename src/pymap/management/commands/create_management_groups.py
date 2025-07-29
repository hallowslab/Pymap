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
        self, group_name: str, model: type[Model]|None=None, group_permissions: list[str] = []
    ) -> None:
        
        def has_permission(group: Group, perm: Permission) -> bool:
            return group.permissions.filter(codename=perm.codename).exists()

        # Add permissions to the group
        def add_permissions(permissions: list[str]) -> None:
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

        # Get or create the group
        group, created = Group.objects.get_or_create(name=group_name)

        # Output message based on whether the group was created or already existed
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created group "{group_name}"'))
        else:
            self.stdout.write(self.style.NOTICE(f'Group "{group_name}" already exists'))

        # Only add model permissions if model is provided
        if model is not None:
            model_content_type = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(content_type=model_content_type).filter(
                codename__in=group_permissions
            )
            add_permissions(permissions)

        # Save the group
        group.save()

    def handle(self, *args: object, **options: Any) -> None:
        # Create User Managers group
        self.manage_group(
            group_name="User Managers",
            model=User,
            group_permissions=["add_user", "change_user", "delete_user", "view_user"],
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
        self.manage_group(
            "Config manager",
            None,
            []
        )
