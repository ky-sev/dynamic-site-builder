# Purpose

The `app/` directory serves as the application composition and bootstrap layer. It handles cross-cutting concerns, environment configuration, database connection lifecycles, global authentication/authorization guards, and web framework (FastAPI) startup lifespans. It wires together domain modules and external gateways into an executable application without containing core business logic.

# When to add

Add files or modules to `app/` when you need to:
- Define or load application configuration, secrets, or environment variables (`app/config/`).
- Initialize and configure database engines, connection pools, or session factories (`app/database/`).
- Implement global security guards, authentication middlewares, API token verifiers, or authorization handlers (`app/security/`).
- Configure application startup/shutdown lifespans, global exception handlers, middleware pipelines, or root router registration (`app/startup/`).

**Do NOT add here:**
- Business logic or domain rules (place in `domains/`).
- Third-party client wrappers or integration adapters (place in `gateways/`).

