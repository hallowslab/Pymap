from typing import Any
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandParser
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string


class Command(BaseCommand):
    help = "Resets the password for the supplied user, to a randomly generated one"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("username", type=str, help="Username of the account")
        parser.add_argument(
            "--length",
            type=int,
            default=20,
            choices=range(15, 21),
            help="Length of the new password to be generated",
        )
        return super().add_arguments(parser)

    def handle(self, *args: object, **options: Any) -> None:
        username = options["username"]
        length = options["length"]
        try:
            UserModel = get_user_model()
            user = UserModel.objects.get(username=username)

            _new_password = get_random_string(length)
            user.set_password(_new_password)
            if not user.check_password(_new_password):
                self.stderr.write(
                    self.style.ERROR(
                        f"We were unable to set the password to {_new_password}"
                    )
                )
                return
            self.stdout.write(
                self.style.SUCCESS(
                    f"Password for user {username} has been updated to {_new_password}"
                )
            )
            user.save()
        except ObjectDoesNotExist:
            self.stderr.write(self.style.ERROR(f"User {username} does not exist"))
