# Migration Policy

Status: Django migrations are implemented and applied in the local development database. There is no hosted deployment or automated migration-at-startup process.

Use Django migrations versioned with the models. Generate during development, inspect operations/SQL and apply via one explicit migration step per environment. Do not run competing migrations from every web process.

The initial migration includes the custom user model. Plan dependencies across apps using accepted FKs; do not introduce circular migration imports. PostgreSQL-backed tests cover database behavior. For a fresh local database, run `uv run python manage.py migrate` explicitly after Compose reports PostgreSQL healthy; application startup does not run migrations. Before hosted rollout, add clean-install and upgrade tests from each supported schema version with representative fictional rows.

Use expand/contract: add compatible fields/tables, backfill in bounded batches, deploy compatible readers/writers, enforce constraints only after validation, remove obsolete structures later. Potential long locks, table rewrites and concurrent index operations need specific review against actual table sizes.

Default recovery is a forward fix. An explicitly reversible migration can be reversed only after checking data and application compatibility. Reversing a schema change cannot restore deleted business data. Destructive changes require explicit user authorization, known targets and a verified recovery plan; no delegated architecture choice grants blanket destructive execution.

Migration role should be separated from the runtime role at deployment design; exact credentials/grants remain deferred. Before hosted persistent data: select backup retention, RPO/RTO, restoration verification and rollback-compatible artifact policy.
