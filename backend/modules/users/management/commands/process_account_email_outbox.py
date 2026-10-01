from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from modules.users.email_outbox import process_account_email_outbox


class Command(BaseCommand):
    help = "Deliver a bounded batch of durable account emails through the configured backend."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--batch-size", type=int, default=100)

    def handle(self, *args: object, **options: Any) -> None:
        del args
        batch_size = options["batch_size"]
        if not 1 <= batch_size <= 1000:
            raise CommandError("Batch size must be between 1 and 1000.")
        result = process_account_email_outbox(limit=batch_size)
        self.stdout.write(
            "account_email_outbox "
            f"attempted={result.attempted} delivered={result.delivered} "
            f"retried={result.retried} dead_lettered={result.dead_lettered}."
        )
