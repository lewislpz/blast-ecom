# Actors

Status: Accepted initial design; not implemented.

| Actor | Capabilities | Boundary |
|---|---|---|
| Visitor | Browse active catalog, register/login locally | Cannot access orders or alter inventory |
| Customer | Create orders, view own history, simulate own payment, cancel eligible own orders | Account required; never chooses server price/status |
| Staff administrator | Catalog management, audited stock actions, order inspection/eligible cancellation | Named permissions and restricted Django admin; not arbitrary table edits |
| Local maintainer | Run documented expiry/delivery and development setup commands | Trusted development environment; no public control endpoint |

Maintenance is an application process, not a human identity or a new business domain. Customer and staff authorization details are in the [security baseline](../security/overview.md). External payment, delivery and identity providers are not selected integrations.
