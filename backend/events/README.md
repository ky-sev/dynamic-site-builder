# Purpose

The `events/` directory defines domain events and the internal event bus mechanism that enables asynchronous, decoupled communication between bounded contexts. Instead of one domain directly invoking another domain's services, state changes publish events that other domains can react to independently.

Structure:
- `handlers/`: Event listeners and subscribers that react to published domain events.
- `publishers/`: Event publishing mechanisms (in-memory event bus or integration dispatchers).

# When to add

Add files or modules to `events/` when you need to:
- Define an immutable record of something significant that happened in the business domain (e.g., `DealIntakeSubmitted`, `WorkflowPublished`, `ContractSigned`).
- Add a new event handler that performs a secondary action when an event occurs (e.g., triggering a notification or populating a reporting read model).
- Update event dispatching rules or middleware (e.g., event logging, transaction outbox hooks).

**Do NOT add here:**
- Synchronous direct business operations that must happen within the primary database transaction (place in the respective domain's `services/`).
- External broker drivers like raw Kafka/RabbitMQ client configuration (place in `gateways/`).

