# ADR-0009: API Framework

## Status

Accepted

## Date

2026-09-28

## Context

The accepted Django backend needs an API layer for React. The user requested a recommendation after comparing Django REST framework (DRF) and Django Ninja, then confirmed DRF.

## Decision Drivers

- Consistent validation, permissions and resource handling.
- Integration with Django and separation of transport from domain rules.

## Options Considered

| Option | Advantages | Costs and risks |
|---|---|---|
| Django REST framework | Serializers, permission abstractions and reusable API views | Learning its abstractions; OpenAPI tooling requires selection; generic CRUD can obscure domain workflows |
| Django Ninja | Typed function endpoints, schemas and automatic OpenAPI | Different permission/operation conventions; migration requires endpoint and validation changes |

Both operate within Django. Neither requires another service or guarantees workload capacity.

## Decision

Use **Django REST framework** for the backend HTTP API layer.

## Approval

The project owner answered "si" to "¿Confirmamos Django REST framework?" on 2026-09-28. This selects DRF without authorizing application implementation or additional dependencies.

## Consequences

### Positive

Consistent API serialization, validation and permission mechanisms within Django.

### Negative

DRF abstractions must be learned; versions and OpenAPI tooling need separate choices.

### Risks

Order transitions and inventory reservations must not become unrestricted model CRUD. Permission mechanisms do not define business authorization policies. Business logic remains separate from API handling under existing project principles.

## Reversibility

Moderately expensive to expensive once endpoints, serializers and permission integrations accumulate. Stable external contracts and separated domain logic can limit migration scope.

## Reconsideration Trigger

Demonstrated requirements or maintenance costs that justify changing the API layer.

## Related Decisions

- [Backend Stack](ADR-0006-backend-stack.md).
- [Application Architecture](ADR-0002-application-architecture.md).
- [Initial Domain Boundaries](ADR-0004-initial-domain-boundaries.md).

## Notes

Versions, OpenAPI generator, authentication, permission policies, pagination, errors and routes remain pending. No package is installed by this record.

Previously consulted references: [DRF](https://www.django-rest-framework.org/) and [Django Ninja](https://django-ninja.dev/).
