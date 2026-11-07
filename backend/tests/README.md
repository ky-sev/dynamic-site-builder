# Purpose

The `tests/` directory hosts the test suite for the backend application, structured to validate behavior across different testing layers:
- `unit/`: Fast, isolated tests for domain entities, validation rules, utility functions, and business services using in-memory mocks.
- `integration/`: Tests verifying interaction between domain repositories, databases, gateways, and external adapters.
- `e2e/`: End-to-end tests evaluating the complete FastAPI HTTP request/response cycle, authentication, and database persistence.

# When to add

Add files or modules to `tests/` when you need to:
- Test domain logic, schemas, and service invariant rules (`tests/unit/`).
- Validate database repository queries, migrations, or gateway adapter integrations (`tests/integration/`).
- Write full API lifecycle tests covering endpoints from route down to database (`tests/e2e/`).
- Define shared test fixtures, test databases, mock clients, or factory helpers (e.g., `conftest.py`).

**Do NOT add here:**
- Production code or runtime dependencies.

