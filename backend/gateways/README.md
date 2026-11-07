# Purpose

The `gateways/` directory contains outbound infrastructure adapters in accordance with Hexagonal (Ports and Adapters) architecture. It encapsulates external systems, third-party APIs, communication protocols, and storage drivers (e.g., PostgreSQL, Redis, Kafka, Email services, Quickbase). By isolating these details in gateways, domain logic remains decoupled from third-party vendor APIs and low-level protocol nuances.

# When to add

Add a new subfolder or client adapter to `gateways/` when you need to:
- Connect to an external platform or third-party service (e.g., `gateways/quickbase/`, `gateways/email/`).
- Implement cache clients, key-value stores, or session caching (e.g., `gateways/redis/`).
- Implement external message brokers or streaming publishers/consumers (e.g., `gateways/kafka/`).
- Provide raw storage drivers, connection pooling abstractions, or low-level database utilities (e.g., `gateways/postgres/`).

**Do NOT add here:**
- Business logic or domain state validation (place in `domains/`).
- Domain-level repository interfaces (place in `domains/<domain>/repositories/`).
- App startup configuration or FastAPI lifecycle wiring (place in `app/`).

