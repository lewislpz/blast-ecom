# HTTP API Standards

Status: Accepted design; no endpoint or OpenAPI artifact exists. [ADR-0017](../decisions/ADR-0017-http-api-contract.md).

## Contract

JSON under /api/v1/, lower-case plural resources, snake_case fields, UUID strings, UTC ISO-8601 timestamps and two-decimal money strings with currency EUR. Generated OpenAPI 3 through drf-spectacular is reviewed/versioned with implementation; use openapi-typescript to produce frontend types. Pin compatible generators and test schemas; generated types are not runtime authorization.

## Initial Routes

| Method | Path | Access | Success |
|---|---|---|---|
| GET | /api/v1/auth/csrf/ | Public | 200 token/bootstrap; no-cache |
| POST | /api/v1/auth/register/ | Local registration; CSRF | 201 customer summary |
| POST | /api/v1/auth/login/ | Public; CSRF | 200 identity and session cookie |
| POST | /api/v1/auth/logout/ | Session; CSRF | 204 |
| GET | /api/v1/auth/me/ | Active session | 200 own identity |
| POST | /api/v1/auth/password-reset/ | Local mail flow; CSRF | 202 generic response |
| POST | /api/v1/auth/password-reset/confirm/ | Valid Django reset token; CSRF | 204 |
| GET | /api/v1/categories/ | Public, active only | 200 paginated |
| GET | /api/v1/products/ | Public, active only | 200 paginated |
| GET | /api/v1/products/{id}/ | Public, active only | 200 |
| POST | /api/v1/orders/ | Customer; CSRF + idempotency | 201 initial order |
| GET | /api/v1/orders/ | Customer, own records | 200 paginated |
| GET | /api/v1/orders/{id}/ | Owner | 200 current order |
| POST | /api/v1/orders/{id}/payment/ | Owner; CSRF + idempotency | 200 simulation outcome |
| POST | /api/v1/orders/{id}/cancel/ | Owner; CSRF + idempotency | 200 cancelled order |
| GET | /health/live/ | Deployment health surface | 200 process alive |
| GET | /health/ready/ | Deployment health surface | 200 DB reachable; 503 otherwise |

Health endpoints sit outside the business API version. Admin operations use Django admin and domain services, not a parallel public CRUD API. Readiness must not leak DB errors.

## Order Creation Body

items is a list of product_id, quantity and expected_unit_price. delivery_address carries the documented address fields. The backend determines owner, price, currency, states and totals. Reject unknown fields; reject changed price with 409 rather than silently charging a new price. Never accept card numbers. Payment/cancel bodies are empty; simulator outcomes are not client parameters.

Responses include id, state, items with snapshots, subtotal, shipping_total, total, currency, expires_at and timestamps. Address is returned only to owner/authorized staff. Payment response reports succeeded or failed as a domain outcome (200), not a server error. Do not include internal permission flags or hashes in customer summaries.

## Lists

Page-number pagination, page_size default 20 and max 100, count/next/previous/results envelope. Products: category filter and ordering by title or price, with UUID tie-breaker; default title,id. Orders: own state filter, default -created_at,-id. No arbitrary ORM lookup/filter parameters. Limit bodies to 64 KiB initially and product/order bounds as documented; these defaults are adjustable after tests.

## Errors

Use application/problem+json per RFC 9457: type (about:blank initially), title, status, safe detail, code, request_id and optional field_errors [{field, code, message}]. Never include stack traces or SQL. Success uses resource bodies, not a global success wrapper.

400 malformed/invalid input; 403 unauthenticated or forbidden session requests (consistent with DRF SessionAuthentication), including CSRF; 404 absent or inaccessible resources; 409 state/stock/price/idempotency conflict; 429 throttled; 503 temporary dependency failure. Distinguish AUTH_REQUIRED from PERMISSION_DENIED and CSRF_FAILED by code. API clients use code, not English prose. Infrastructure errors get a server-generated request_id in X-Request-ID; inbound arbitrary IDs are not trusted.

## Evolution

Additive compatible changes stay in v1. Breaking changes require a new version and a migration/deprecation plan. Initial error text is English; React provides user-facing Spanish labels, without changing stable codes. Do not infer multilingual product content.

Sources: [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html), [DRF schema guidance](https://www.django-rest-framework.org/api-guide/schemas/), [drf-spectacular](https://drf-spectacular.readthedocs.io/en/latest/).
