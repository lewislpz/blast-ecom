# Product Overview

Blast Ecom is a planned single-seller physical-goods store with EUR pricing. The accepted v1 includes a customer web experience, internal administration, inventory reservations, orders, simulated payment and simulated notifications.

Initial behavior is defined in [scope](scope.md) and [purchase workflow](purchase-workflow.md). Customers register before checkout; staff use a restricted Django admin. One logical stock pool serves the initial model.

The long-term distributed/operational vision remains conditional on requirements; the initial backend is a Django modular monolith. This workspace contains documentation only.

Local simulated delivery addresses, EUR 0.00 shipping and demo prices enable development without pretending to know tax jurisdiction or logistics policy. Real commercial use, privacy requirements, team capacity, workload and search-acquisition goals remain inputs before public launch.
