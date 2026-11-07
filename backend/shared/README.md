# Purpose

The `shared/` directory is the Shared Kernel across the backend. It contains domain-agnostic utilities, common data structures, base exception hierarchies, pagination helpers, and generic type definitions that are reused across multiple domains and gateways without introducing tight cross-domain coupling.

# When to add

Add files or modules to `shared/` when you need to:
- Define base domain exception classes (e.g., `DomainException`, `EntityNotFoundException`, `ValidationException`).
- Implement reusable pagination schemas or query parameter helpers (`pagination.py`).
- Provide common type aliases, custom scalar types, or UUID/timestamp formatters (`types.py`).
- Implement utility functions that are strictly generic and contain no business logic.

**Do NOT add here:**
- Domain-specific logic, schemas, or models (e.g., deal schemas or intake validators belong in their respective `domains/` folders).
- Configuration variables or environment secrets (place in `app/config/`).
- Database connection sessions or ORM engines (place in `app/database/`).

