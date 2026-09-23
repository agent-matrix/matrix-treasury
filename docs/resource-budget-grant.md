# Resource budget grant

Matrix Treasury's role in the Agent-Matrix cognition loop is **resource
authorization**, not mandatory blockchain finance.

`POST /v1/budget/grant` receives an already-proposed plan and returns a bounded
BudgetGrant with:

- maximum MXU,
- maximum tokens,
- maximum runtime seconds,
- maximum tool calls (extension field),
- hard-stop semantics.

Every dimension is capped by operator configuration. A plan that requests more
than the ceiling is constrained, never allowed to silently exceed it.

Blockchain settlement, multi-currency vaults, credit, and cross-chain features
remain optional Treasury modules and are not prerequisites for Matrix OS.
