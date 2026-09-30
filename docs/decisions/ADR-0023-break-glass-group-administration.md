# ADR-0023: Break-Glass Group Administration

## Status

Accepted

## Date

2026-09-30

## Context

Django's built-in Group administration lets users who can change a group edit its permission set. A staff member who has `auth.change_group` through a group can therefore add a privileged permission to that same group and escalate their own access. A PostgreSQL-backed regression test reproduced this path before the change: the admin accepted the POST (302) and the permission was granted.

## Decision Drivers

- Prevent staff from granting themselves or their groups additional privileges.
- Preserve an explicit recovery path for trusted local development administration.
- Keep permissions explicit and the control easy to test and operate.

## Options Considered

### Remove Group administration

Unregister Django's Group model from the admin.

Advantages:

- Smallest exposed administrative surface.
- No admin path for changing group permissions.

Disadvantages:

- Group maintenance requires an alternative management mechanism or direct database work.
- Less convenient for the local development workflow.

### Restrict Group administration to active superusers

Replace the default GroupAdmin with one that requires an active, staff, superuser account for module, view, add, change, and delete access.

Advantages:

- Closes the tested self-escalation route for ordinary staff.
- Retains a clear break-glass route for local setup and recovery.
- Uses Django's existing superuser model without introducing another role system.

Disadvantages:

- Superuser credentials remain highly privileged and must not be used for routine work.
- This control does not replace production staff provisioning, MFA, or centralized audit monitoring.

### Add permission-change-specific approval logic

Allow ordinary staff to manage groups while validating permission diffs and preventing privilege grants beyond an administrator's own authority.

Advantages:

- Could support delegated role administration.

Disadvantages:

- More complex policy and edge cases around inherited permissions, multiple groups, and concurrent changes.
- Not required for the initial local development scope.

## Decision

Use a custom GroupAdmin restricted to active staff superusers for every Group admin action. Ordinary staff cannot view or mutate groups through Django admin. Superusers are a break-glass mechanism and are not routine operators.

This decision was made by Codex under the project owner's explicit instruction to continue recommended implementation autonomously and finish the development slice. It applies to this bounded security remediation, not unrelated future architectural choices.

## Consequences

### Positive

- A staff member cannot use `auth.change_group` to grant its own group additional permissions through Django admin.
- The denied path and intended superuser recovery path are covered by PostgreSQL-backed tests.

### Negative

- Ordinary staff cannot administer group membership or permissions through the built-in Django admin.
- Local bootstrap and recovery that require group edits must use the break-glass superuser.

### Risks

- Protect superuser credentials and keep their use rare. Before shared or public deployment, define staff provisioning, MFA/access restrictions, and monitored audit procedures.

## Reversibility

Easy to reverse in code, but widening the policy requires new authorization tests and security review.

## Reconsideration Trigger

Introduce delegated role administration only when a concrete operational need exists and a reviewed policy can prevent privilege escalation.

## Related Decisions

- [ADR-0016: Identity and Administration](ADR-0016-identity-and-administration.md)
- [Security overview](../security/overview.md)
- [Initial threat model](../security/threat-model.md)
