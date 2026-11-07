# Dynamic Site Builder _(dynamic-site-builder)_

Workflow configuration editor, schema validator, and live form preview engine.

Dynamic Site Builder (also known as `json-site`) is a full-stack platform designed to build, preview, and manage data-driven workflows using JSON schemas. It provides an Angular administrative UI paired with an Express Server-Side Rendering (SSR) proxy layer, a FastAPI backend for validation and version control, and a PostgreSQL database storing schema versions as versioned JSONB documents.

> Note: The repository and root directory are named `dynamic-site-builder`, while the internal frontend package and SSR artifacts are labeled `json-site`.

## Table of Contents

- [Security](#security)
- [Background](#background)
- [Install](#install)
- [Usage](#usage)
- [API](#api)
- [Maintainers](#maintainers)
- [Contributing](#contributing)
- [License](#license)

## Security

Administrative actions (such as publishing new workflow versions, inspecting version deployment history, and rolling back configurations) require bearer token authentication.

- Configure `WORKFLOW_ADMIN_TOKEN` with a strong, cryptographically secure token.
- Pass the token in the `Authorization` header as `Bearer <WORKFLOW_ADMIN_TOKEN>` for protected endpoints.
- In the web interface, the admin token is kept only within the active browser session state and is never written to disk or local storage.
- Never commit `frontend/env.local` or environment files to version control.
- Avoid using default database passwords in production environments.
- Payload limits: The API enforces a 1 MB payload limit to prevent resource exhaustion attacks.

## Background

Many business applications require flexible data intake forms (e.g., deal pipelines, user onboarding, dynamic intake questionnaires) that evolve faster than underlying database migrations and UI release cycles.

Dynamic Site Builder resolves this by decoupling the form definition from client code:
- **Declarative Schemas:** Workflows and fields are declared in standard JSON structures.
- **Dynamic Field Types:** Out-of-the-box support for `text`, `yesNo`, `dropdown`, `textarea`, `number`, and `date` fields.
- **Audit & Version History:** Every publication generates an immutable, sequential version snapshot, allowing safe rollbacks at any point.
- **Preview Execution:** Administrators can test input validation and review real-time JSON state before activating changes in live environments.

## Install

### Dependencies

Ensure the following prerequisites are installed on your host machine:

- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) (Recommended for containerized execution)
- [Node.js](https://nodejs.org/) (v22 or newer) and [npm](https://www.npmjs.com/) (v11 or newer)
- [Python](https://www.python.org/) (v3.12 or newer)
- [PostgreSQL](https://www.postgresql.org/) (v17 or compatible, if running without Docker)

### Setup Environment

Initialize your local environment file from the provided example:

```powershell
Copy-Item frontend\env.local.example frontend\env.local
```

Edit `frontend/env.local` to define your secrets:

```env
WORKFLOW_ADMIN_TOKEN=your-secure-random-token
POSTGRES_PASSWORD=your-secure-db-password
APP_PORT=4000
```

### Installation with Docker Compose

Build and launch all services (PostgreSQL, FastAPI API, and Angular SSR UI):

```powershell
docker compose --env-file frontend\env.local up --build
```

Access the UI at `http://localhost:4000`.

To tear down containers:

```powershell
docker compose --env-file frontend\env.local down
```

To stop containers and wipe persistent PostgreSQL volumes:

```powershell
docker compose --env-file frontend\env.local down --volumes
```

### Manual Installation (Without Docker)

#### 1. Database Setup

Ensure PostgreSQL is running and initialize the database schema:

```powershell
psql -h localhost -U workflow -d workflows -f backend\migrations\001_workflow_versions.sql
```

#### 2. Backend API Setup

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### 3. Frontend UI Setup

```powershell
Set-Location ..\frontend
npm install --legacy-peer-deps
npm run build
```

## Usage

### Running Locally (Without Docker)

#### 1. Start FastAPI Service

From the `backend` directory with the virtual environment active:

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Check API health at `http://localhost:8000/health`.

#### 2. Start Angular SSR Server

In a separate terminal, from the `frontend` directory:

```powershell
$env:WORKFLOW_API_URL = "http://127.0.0.1:8000"
npm run serve:ssr:json-site
```

Visit the application at `http://localhost:4000`.

### Workflow Admin Interface

1. **Load Workflow:** Enter a key (e.g., `deal_flow`) and fetch active definitions. If uninitialized, the sample schema ([`examples/deal-flow.json`](./examples/deal-flow.json)) is loaded.
2. **Schema Editing & Validation:** Modify form fields in the JSON editor. The interactive form renders instantaneously and highlights validation errors.
3. **Form Preview:** Enter form values in the rendered fields to observe real-time serialized JSON output.
4. **Publishing Versions:** Supply the author identifier (`updated_by`), commit message, and `WORKFLOW_ADMIN_TOKEN`, then trigger publish.
5. **Rollback:** Navigate deployment history and restore any previous version with zero downtime.

### Testing and Building

#### Frontend Tests and Build

```powershell
Set-Location frontend
npm run build
npm test
```

#### Backend Tests

```powershell
Set-Location backend
python -m pytest
```

## API

The backend exposes REST endpoints directly on port 8000 and proxied via the SSR layer under `/api`.

### Endpoints Overview

| Method | Path | Access | Description |
| --- | --- | --- | --- |
| `GET` | `/api/workflow/{key}` | Public | Retrieve the active schema definition and version number. |
| `GET` | `/api/workflow/{key}/versions` | Admin | Retrieve deployment history and previous versions. |
| `POST` | `/api/workflow/{key}/version` | Admin | Validate schema and publish a new active version. |
| `PUT` | `/api/workflow/{key}/rollback/{version}` | Admin | Re-activate an existing version without history loss. |
| `GET` | `/health` | Public | API service health check. |

### Publish Workflow Payload

```json
{
  "schema_data": {
    "title": "Deal intake",
    "description": "Capture details for a new deal.",
    "fields": [
      {
        "key": "dealName",
        "label": "Deal name",
        "type": "text",
        "required": true
      },
      {
        "key": "dealStage",
        "label": "Deal stage",
        "type": "dropdown",
        "required": true,
        "options": ["Lead", "Qualified", "Proposal", "Closed Won", "Closed Lost"]
      }
    ]
  },
  "updated_by": "admin@example.com",
  "commit_message": "Add deal intake schema with stage dropdown"
}
```

### Schema Rules

- **Workflow Key:** 1 to 50 characters, containing only alphanumeric characters, underscores (`_`), and hyphens (`-`).
- **Supported Field Types:** `text`, `yesNo`, `dropdown`, `textarea`, `number`, `date`.
- **Dropdown Fields:** Must provide a non-empty list of string values under `options`.
- **Field Keys:** Must be unique within the workflow schema.

## Maintainers

- [@ky-sev](https://github.com/ky-sev)

## Contributing

Contributions, bug reports, and feature requests are welcome!

- **Questions & Issues:** Please submit an issue via the [GitHub Issues](https://github.com/ky-sev/dynamic-site-builder/issues) tracker.
- **Pull Requests:** PRs are accepted. Please ensure all backend unit tests (`pytest`) and frontend test suites (`npm test`) pass prior to opening a PR.

## License

MIT © [ky-sev](https://github.com/ky-sev)
