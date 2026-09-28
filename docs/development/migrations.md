# Migration Policy

Status: Accepted procedure design; no migration files or deployment exist.

Use Django migrations versioned with the models. Generate during development, inspect operations/SQL and apply via one explicit migration step per environment. Do not run competing migrations from every web process.

First migration includes the custom user model. Plan dependencies across apps using accepted FKs; do not introduce circular migration imports. Tests cover clean installation and upgrade from the previous schema with representative fictional rows.

Use expand/contract: add compatible fields/tables, backfill in bounded batches, deploy compatible readers/writers, enforce constraints only after validation, remove obsolete structures later. Potential long locks, table rewrites and concurrent index operations need specific review against actual table sizes.

Default recovery is a forward fix. An explicitly reversible migration can be reversed only after checking data and application compatibility. Reversing a schema change cannot restore deleted business data. Destructive changes require explicit user authorization, known targets and a verified recovery plan; no delegated architecture choice grants blanket destructive execution.

Migration role should be separated from the runtime role at deployment design; exact credentials/grants remain deferred. Before hosted persistent data: select backup retention, RPO/RTO, restoration verification and rollback-compatible artifact policy.
