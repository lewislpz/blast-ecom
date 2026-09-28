# Frontend Conventions

Status: Accepted design; no frontend files exist. [ADR-0018](../decisions/ADR-0018-frontend-conventions.md).

- React Router declarative routing for catalog, product, cart, login/register, checkout and own orders.
- TanStack Query for catalog/orders/session-related server state. Explicit stale/invalidation policies by resource; no default retry of mutations.
- A fetch adapter sends credentials and CSRF header, decodes Problem Details and preserves idempotency keys. Query errors distinguish login required, stock conflict and temporary server failure.
- Generated openapi-typescript types in shared/api; generated files are not edited manually. Schema/type generation must be reproducible.
- Cart context holds UUID/quantity in memory, never passwords, authoritative prices or server state. Logout/reload clears it. Order state is refetched after an idempotency replay.
- Native controlled forms, explicit labels and error associations; no form/schema library until complexity justifies one. Server validation is authoritative.
- CSS Modules and shared CSS custom properties. No mandatory Tailwind/component library. Plain-text product descriptions; static local image references only.
- Spanish initial interface, English code/contract fields. Accessible keyboard flows, focus after errors/navigation, clear disabled states and responsive layout.
- Cancel action shown only for awaiting_payment before the displayed deadline; backend rechecks regardless of UI. Confirmed does not mean shipped.
- Demo checkout labels simulated payment/shipping and no real sale. Price changes require reconfirmation.

Vite produces frontend static artifacts. No production Vite dev server. Same-origin /api and /admin proxy; SPA route fallback must not swallow API/admin errors. Public SEO goals remain an explicit launch input.

Sources: [React Router](https://reactrouter.com/start/declarative/installation), [TanStack Query](https://tanstack.com/query/latest/docs/framework/react/overview), [Vite](https://vite.dev/guide/).
