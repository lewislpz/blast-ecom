# HTTP API Standards

Status: Catalog read endpoints, same-origin session/CSRF account endpoints, owner-scoped order endpoints, and PostgreSQL-backed authentication attempt limits are implemented. Registration is restricted to local DEBUG mode; password reset and public-account protections are deferred. [ADR-0017](../decisions/ADR-0017-http-api-contract.md), [ADR-0024](../decisions/ADR-0024-authentication-attempt-limits.md).

## Contract

JSON under /api/v1/, lower-case plural resources, snake_case fields, UUID strings, UTC ISO-8601 timestamps and two-decimal money strings with currency EUR. Generated OpenAPI 3 through drf-spectacular is reviewed/versioned with implementation; use `@hey-api/openapi-ts` to produce frontend types from `backend/openapi.yaml`. Pin compatible generators and test schemas; generated types are not runtime authorization. See [ADR-0022](../decisions/ADR-0022-api-type-generator.md).

## Initial Routes

| Method | Path | Access | Success |
|---|---|---|---|
| GET | /api/v1/auth/csrf/ | Public | 200 token/bootstrap; no-cache |
| POST | /api/v1/auth/register/ | Local DEBUG only; CSRF | 201 customer summary; 404 otherwise |
| POST | /api/v1/auth/login/ | Public; CSRF | 200 identity and rotated session cookie |
| POST | /api/v1/auth/logout/ | Session; CSRF | 204 and session revocation |
| GET | /api/v1/auth/me/ | Active session | 200 own identity |
| GET | /api/v1/categories/ | Public, active only (implemented) | 200 paginated |
| GET | /api/v1/products/ | Public, active only (implemented) | 200 paginated; filters: category, ordering; includes `in_stock` boolean |
| GET | /api/v1/products/{id}/ | Public, active only (implemented) | 200 |
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

Unsafe session and customer operations require the `X-CSRFToken` header, obtained from the no-store CSRF bootstrap endpoint. The CSRF cookie is HttpOnly; clients use the token returned in the bootstrap JSON. Fetch a fresh token after login/logout rotation. Login failures use one generic response for unknown email, wrong password and staff accounts. Customer sessions expire after 12 hours; staff sessions after one hour. Registration is available only with `DEBUG=true` and is not a public registration mechanism. Password reset endpoints do not exist.

Order creation and state-changing actions require UUIDv4 `Idempotency-Key`; keys are scoped by customer and operation. Responses include id, state, items with snapshots, subtotal, shipping_total, total, currency, expires_at and timestamps. Address is returned only in the owner's detail response. Payment response reports succeeded or failed as a domain outcome (200), not a server error. Do not include internal permission flags or hashes in customer summaries.

## Lists

Page-number pagination, page_size default 20 and max 100, count/next/previous/results envelope. Products: category filter and ordering by title or price, with UUID tie-breaker; default title,id. Orders: own state filter, default -created_at,-id. No arbitrary ORM lookup/filter parameters. Limit bodies to 64 KiB initially and product/order bounds as documented; these defaults are adjustable after tests.

## Errors

Use application/problem+json per RFC 9457: type (about:blank initially), title, status, safe detail, code, request_id and optional field_errors [{field, code, message}]. Never include stack traces or SQL. Success uses resource bodies, not a global success wrapper.

The implemented DRF exception handler emits this media type for handled API errors, creates a server-side request ID and maps validation errors to `field_errors`. A 64 KiB request body cap applies to `/api/v1/`. The generated schema at `backend/openapi.yaml` documents CSRF and idempotency headers; regenerate and validate it with `uv run python manage.py spectacular --file openapi.yaml --validate` from `backend/`.

400 malformed/invalid input; 403 unauthenticated or forbidden session requests (consistent with DRF SessionAuthentication), including CSRF; 404 absent or inaccessible resources; 409 state/stock/price/idempotency conflict; 429 throttled; 503 temporary dependency failure. Distinguish AUTH_REQUIRED from PERMISSION_DENIED and CSRF_FAILED by code. API clients use code, not English prose. Infrastructure errors get a server-generated request_id in X-Request-ID; inbound arbitrary IDs are not trusted.

Customer login and local registration may return HTTP 429 Problem Details with `code=RATE_LIMITED` and `Retry-After` when a configured PostgreSQL fixed-window limit is exceeded. The Django Admin login uses the same attempt policy and returns a generic 429 response. Counters are shared across app processes and store only HMAC-pseudonymous keys. Database errors fail closed through the generic 503 handling. These are application-level abuse controls, not protection against distributed attacks or volumetric denial of service.

## Evolution

Additive compatible changes stay in v1. Breaking changes require a new version and a migration/deprecation plan. Initial error text is English; React provides user-facing Spanish labels, without changing stable codes. Do not infer multilingual product content.

Sources: [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html), [DRF schema guidance](https://www.django-rest-framework.org/api-guide/schemas/), [drf-spectacular](https://drf-spectacular.readthedocs.io/en/latest/).
