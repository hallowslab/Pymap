from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CeleryTask


class UserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["id", "username"]


class CeleryTaskSerializer(serializers.ModelSerializer[CeleryTask]):
    owner = UserSerializer()  # UserSerializer required for the owner field

    # Don't use __all__ so that we are able to check order by against Meta.fields
    class Meta:
        model = CeleryTask
        fields = [
            "task_id",
            "source",
            "destination",
            "log_path",
            "n_accounts",
            "domains",
            "archived",
            "finished",
            "start_time",
            "run_time",
            "custom_label",
            "owner",
        ]


class TaskIdListSerializer(serializers.Serializer):
    task_ids = serializers.ListField(child=serializers.CharField())
