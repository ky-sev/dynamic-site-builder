# Purpose

The `domains/` directory hosts the core business capabilities (Bounded Contexts) of the platform. Each domain represents an autonomous, cohesive slice of the problem domain with its own ubiquitous language, business rules, entities, and validation invariants.

Each domain is organized into:
- `api/`: REST route controllers and HTTP request/response handlers for this domain.
- `models/`: Domain entities, value objects, and database ORM/relational mappings.
- `repositories/`: Persistence abstraction interfaces and query implementations.
- `schemas/`: Pydantic data transfer objects (DTOs), input payloads, and response contracts.
- `services/`: Core business workflows, state machines, domain rule validations, and orchestration.

# When to add

Add a new subfolder or logic to `domains/` when you need to:
- Introduce a new business capability or lifecycle (e.g., `workflow_engine`, `intake`, `opportunities`, `reporting`).
- Enforce business invariants (e.g., checking funding status before signing a contract).
- Expose domain-specific endpoints or contracts.
- Add queries or operations that belong to an existing domain's aggregate root.

**Do NOT add here:**
- Infrastructure adapters such as raw Kafka publishers or Redis drivers (place in `gateways/`).
- App-wide bootstrap configuration or server startup code (place in `app/`).
- Shared primitives that carry no business logic (place in `shared/`).

