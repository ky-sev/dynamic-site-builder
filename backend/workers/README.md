# Purpose

The `workers/` directory contains asynchronous background task runners, job queues, and scheduled jobs (e.g., Celery, RQ, Arq, or Python background task workers). It offloads long-running, resource-intensive, or periodic operations from the synchronous HTTP request/response loop.

Structure:
- `sync_tasks/`: Periodic sync routines (e.g., polling external systems, batch synchronization with Quickbase/CRMs, or daily report generations).
- Other job worker definitions, task queues, and consumer processes.

# When to add

Add files or modules to `workers/` when you need to:
- Execute scheduled background jobs (e.g., nightly batch data aggregations, audit cleanup).
- Run long-running tasks that should not block an HTTP request (e.g., bulk email dispatch, heavy PDF/report generation).
- Process asynchronous queues populated by events or webhooks.

**Do NOT add here:**
- Synchronous API request handlers (place in `domains/<domain>/api/`).
- Core business rules and domain logic (invoke `domains/<domain>/services/` from workers instead of reimplementing logic here).

