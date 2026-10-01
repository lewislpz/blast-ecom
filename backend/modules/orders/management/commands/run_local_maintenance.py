import time
from argparse import ArgumentParser
from typing import cast

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from modules.common.local_database import is_local_database_host
from modules.common.operations import delete_expired_idempotency_records
from modules.notifications.services import process_pending_intents
from modules.orders.services import expire_due_orders
from modules.users.throttling import delete_expired_auth_attempt_buckets


class Command(BaseCommand):
    help = "Run restartable local expiry, notification processing and idempotency cleanup."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--once", action="store_true", help="Run one bounded pass and exit.")
        parser.add_argument("--interval-seconds", type=int, default=10)
        parser.add_argument("--batch-size", type=int, default=100)

    def handle(self, *args: object, **options: object) -> None:
        del args
        interval = cast(int, options["interval_seconds"])
        batch_size = cast(int, options["batch_size"])
        run_once = cast(bool, options["once"])
        database_host = str(settings.DATABASES["default"].get("HOST", ""))
        if not settings.DEBUG or not is_local_database_host(database_host):
            raise CommandError(
                "run_local_maintenance is restricted to DEBUG with a local database."
            )
        if interval < 1:
            raise CommandError("--interval-seconds must be at least 1.")
        if not 1 <= batch_size <= 1000:
            raise CommandError("--batch-size must be between 1 and 1000.")

        while True:
            expired = expire_due_orders(limit=batch_size)
            notifications = process_pending_intents(limit=batch_size)
            cleaned = delete_expired_idempotency_records(limit=batch_size)
            throttle_buckets = delete_expired_auth_attempt_buckets(limit=batch_size)
            self.stdout.write(
                f"Maintenance pass complete: expired_orders={expired} "
                f"processed_local_notification_intents={notifications.simulated} "
                f"retryable_notification_failures={notifications.failed} "
                f"deleted_expired_idempotency_records={cleaned} "
                f"deleted_expired_auth_attempt_buckets={throttle_buckets}."
            )
            if run_once:
                return
            time.sleep(interval)
