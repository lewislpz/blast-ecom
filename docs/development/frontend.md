# Frontend Conventions

Status: Customer browser journey implemented for local demo; backend/production limitations still apply. [ADR-0018](../decisions/ADR-0018-frontend-conventions.md) and [ADR-0022](../decisions/ADR-0022-api-type-generator.md).

- React Router declarative routing for catalog, product, cart, login/register, checkout and own orders.
- TanStack Query for catalog/orders/session-related server state. Explicit stale/invalidation policies by resource; no default retry of mutations.
- A fetch adapter sends credentials and CSRF header, decodes Problem Details and preserves idempotency keys. Query errors distinguish login required, stock conflict and temporary server failure.
- Generated `@hey-api/openapi-ts` TypeScript types in `src/shared/api/generated`; generated files are not edited manually or reformatted. They are excluded from Prettier so regeneration remains byte-for-byte stable. Run `npm run generate:api-types` from `frontend/` after backend schema changes and review the generated diff.
- Cart context holds UUID/quantity in memory, never passwords, authoritative prices or server state. Logout/reload clears it. Order state is refetched after an idempotency replay.
- Native controlled forms, explicit labels and error associations; no form/schema library until complexity justifies one. Server validation is authoritative.
- Shared CSS custom properties and one global application stylesheet; CSS-module scoping is deferred and the current stylesheet is tracked as maintenance debt. No mandatory Tailwind/component library. Product `image_key` currently uses local CSS-generated artwork rather than remote/user-controlled image URLs.
- Spanish initial interface, English code/contract fields. Accessible keyboard flows, focus after route changes, labelled form controls, live loading/error states, explicit disabled states and responsive layout.
- Cancel action shown only for awaiting_payment before the displayed deadline; backend rechecks regardless of UI. Confirmed does not mean shipped.
- Demo checkout labels simulated payment/shipping and no real sale. Price changes require reconfirmation.
- Address form explicitly requests fictitious data; checkout stores its address in the local order record, and this demo does not connect a shipping provider.
- API credentials are not stored by frontend code. The browser owns the same-origin HttpOnly session cookie; the CSRF token is held in memory only. Cart stores IDs/quantities in memory only and clears on logout/reload.
- Order/payment/cancel mutations use UUIDv4 idempotency keys. Keys are retained for transport uncertainty, replaced after a server response, and are never persisted.

## Implemented Routes

| Route | Behavior |
|---|---|
| `/` | Active product catalog, category filter and local search |
| `/products/:id` | Product detail and add-to-cart |
| `/cart` | In-memory item quantities and estimated subtotal |
| `/login`, `/register` | Session login; local DEBUG-only account registration |
| `/checkout` | Fictitious delivery details and server-authoritative order creation |
| `/account/orders` | Current user's order history and logout |
| `/orders/:id` | Own order detail, payment simulation and eligible cancellation |

Vitest covers catalog/cart rendering and API-client CSRF/error/idempotency contracts. Playwright exercises registration, checkout, simulated payment, cancellation and order history against the running local backend and database. Axe scans the storefront, login and registration pages for critical/serious violations. These local checks are not production-readiness evidence.

Vite produces frontend static artifacts. No production Vite dev server. Same-origin /api and /admin proxy; SPA route fallback must not swallow API/admin errors. Public SEO goals remain an explicit launch input.

Sources: [React Router](https://reactrouter.com/start/declarative/installation), [TanStack Query](https://tanstack.com/query/latest/docs/framework/react/overview), [Vite](https://vite.dev/guide/).
