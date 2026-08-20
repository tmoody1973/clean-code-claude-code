# Product Readiness Rubric

Apply only the dimensions relevant to the product and its risk profile.

## Product intent and user journeys

- Is the intended user and problem clear?
- Are primary flows complete, understandable, and represented in tests or acceptance criteria?
- Are empty, loading, error, cancellation, and recovery states handled?

## Functional correctness

- Do important business rules have executable evidence?
- Are data validation, concurrency, retries, idempotency, and partial failures handled where relevant?
- Are destructive actions scoped, confirmed, and recoverable when practical?

## Security and privacy

- Are authentication and authorization enforced at the correct boundaries?
- Are inputs validated and outputs encoded?
- Are secrets, personal data, permissions, dependencies, and logs handled appropriately?
- Are abuse controls, rate limits, and session behavior appropriate for the product?

## User experience and accessibility

- Can a new user complete the primary journey without hidden knowledge?
- Are keyboard access, focus, labels, contrast, responsive behavior, and error messaging addressed where relevant?
- Does the interface prevent or help recover from costly mistakes?

## Reliability and data safety

- Are timeouts, retries, backups, migrations, rollback, and recovery considered where relevant?
- Are external-service failures visible and contained?
- Can operators diagnose a failed user journey without exposing sensitive data?

## Performance and scale

- Are likely bottlenecks measured or bounded?
- Are queries, payloads, rendering, caching, and background work appropriate for expected use?
- Avoid premature scale work; identify the first credible constraint.

## Delivery and operations

- Are environments, configuration, CI checks, deployment, health checks, and rollback documented?
- Are schema and configuration changes coordinated with deployment order?
- Is ownership of incidents and external dependencies clear?

## Maintainability and handoff

- Can another developer install, run, test, debug, and deploy the product?
- Are architecture, domain terms, integrations, environment-variable names, known risks, and decisions documented?
- Does the repository distinguish current facts from future plans?
