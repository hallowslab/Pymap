from django.contrib import admin
from django.urls import path
from django.http import HttpResponseRedirect
from django.core.management import call_command
from .models import MigrationJob, MigrationTask


@admin.register(MigrationJob)
class MigrationJobAdmin(admin.ModelAdmin):
    change_list_template = "pymap/admin/migrationjob_changelist.html"

    list_display = (
        "id",
        "source_host",
        "dest_host",
        "custom_identifier",
        "status",
        "owner",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "owner",
        "created_at",
    )

    search_fields = (
        "id",
        "source_host",
        "dest_host",
        "custom_identifier",
    )

    readonly_fields = (
        "id",
        "source_host",
        "dest_host",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = ("owner",)

    ordering = ("-created_at",)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "seed-data/",
                self.admin_site.admin_view(self.seed_data),
                name="pymap_migrationjob_seed_data",
            ),
        ]
        return custom_urls + urls

    def seed_data(self, request):
        call_command("seed_pymap")
        self.message_user(request, "Database seeded successfully.")
        return HttpResponseRedirect("../")


@admin.register(MigrationTask)
class MigrationTaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "job",
        "user1",
        "user2",
        "status",
        "terminated",
        "worker_hostname",
        "start_time",
        "end_time",
        "run_time",
        "updated_at",
        "log_path",
    )

    list_filter = (
        "status",
        "terminated",
        "start_time",
    )

    search_fields = (
        "id",
        "user1",
        "user2",
        "credential_ref",
        "worker_hostname",
        "logfile",
    )

    readonly_fields = (
        "id",
        "job",
        "user1",
        "user2",
        "terminated",
        "worker_hostname",
        "start_time",
        "end_time",
        "run_time",
        "updated_at",
        "log_path",
    )

    autocomplete_fields = ("job",)

    ordering = ("-start_time",)
