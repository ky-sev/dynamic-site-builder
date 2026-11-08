import hmac
import json
import logging
import re
from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Path, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from schemas import (
    ActiveWorkflowResponse,
    CreateWorkflowVersionRequest,
    DeployWorkflowResponse,
    RollbackWorkflowResponse,
    WorkflowVersionResponse,
)
from domains.registry import (
    DomainManifest,
    discover_domain_manifests,
    get_domain_default_fixture,
)
from domains.reporting.schemas.report import (
    CreateSubmissionRequest,
    DynamicReportResponse,
)
from domains.reporting.services.report_service import generate_dynamic_report
from settings import settings


logger = logging.getLogger(__name__)
WORKFLOW_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,49}$")
engine = create_engine(settings.sqlalchemy_database_url(), pool_pre_ping=True)
app = FastAPI(title="Workflow API", version="1.0.0")


# Provides the shared SQLAlchemy engine to API routes.
def get_engine() -> Engine:
    return engine


# Validates workflow keys before they are used by API routes.
def validate_workflow_key(key: str = Path(min_length=1, max_length=50)) -> str:
    if not WORKFLOW_KEY_PATTERN.fullmatch(key):
        raise HTTPException(
            status_code=400,
            detail=(
                "Workflow key must be 1-50 characters and contain only letters, "
                "numbers, underscores, or hyphens."
            ),
        )
    return key


# Verifies that an administrative request has a valid bearer token.
def require_admin(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    configured_token = settings.workflow_admin_token
    if configured_token is None or not configured_token.get_secret_value():
        raise HTTPException(
            status_code=503, detail="Workflow administration is not configured."
        )

    scheme, _, supplied_token = (authorization or "").partition(" ")
    if (
        scheme.lower() != "bearer"
        or not supplied_token
        or not hmac.compare_digest(
            supplied_token, configured_token.get_secret_value()
        )
    ):
        raise HTTPException(status_code=401, detail="Invalid admin bearer token.")


WorkflowKey = Annotated[str, Depends(validate_workflow_key)]
Database = Annotated[Engine, Depends(get_engine)]


@app.exception_handler(HTTPException)
# Formats HTTP exceptions as consistent JSON error responses.
async def http_exception_handler(
    _request: Request, exc: HTTPException
) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
# Formats request validation failures as consistent JSON error responses.
async def request_validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = [
        {
            "field": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid request.", "details": errors},
    )


# Logs a database exception and converts it to an HTTP 500 response.
def database_error(fallback: str, error: Exception) -> HTTPException:
    logger.error(
        fallback,
        exc_info=(type(error), error, error.__traceback__),
    )
    return HTTPException(status_code=500, detail=fallback)


@app.get("/health")
# Reports whether the API process is responsive.
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/api/workflow/{key}",
    response_model=ActiveWorkflowResponse,
)
# Returns the active version of a workflow.
def get_active_workflow(key: WorkflowKey, db: Database) -> dict[str, object]:
    try:
        with db.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT schema_data, version
                        FROM workflow_versions
                        WHERE workflow_key = :key AND is_active = TRUE
                        LIMIT 1
                        """
                    ),
                    {"key": key},
                )
                .mappings()
                .first()
            )
    except Exception as error:
        raise database_error("Database reading error.", error) from error

    if row is None:
        default_data = get_domain_default_fixture(key)
        if default_data is not None:
            fixture_version = int(default_data.get("version", 1)) if isinstance(default_data.get("version"), (int, float, str)) and str(default_data.get("version")).isdigit() else 1
            return {"schema_data": default_data, "version": fixture_version}

        raise HTTPException(
            status_code=404, detail="No active workflow configuration found."
        )
    return {"schema_data": row["schema_data"], "version": row["version"]}


@app.get(
    "/api/workflow/{key}/versions",
    response_model=list[WorkflowVersionResponse],
    dependencies=[Depends(require_admin)],
)
# Lists version history for an administrated workflow.
def list_workflow_versions(key: WorkflowKey, db: Database) -> list[dict[str, object]]:
    try:
        with db.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        """
                        SELECT version, is_active, updated_by, commit_message, created_at
                        FROM workflow_versions
                        WHERE workflow_key = :key
                        ORDER BY version DESC
                        """
                    ),
                    {"key": key},
                )
                .mappings()
                .all()
            )
    except Exception as error:
        raise database_error("Database reading error.", error) from error

    return [
        {
            **row,
            "created_at": (
                row["created_at"].isoformat()
                if isinstance(row["created_at"], datetime)
                else str(row["created_at"])
            ),
        }
        for row in rows
    ]


@app.post(
    "/api/workflow/{key}/version",
    response_model=DeployWorkflowResponse,
    dependencies=[Depends(require_admin)],
)
# Creates and activates the next version of a workflow.
def deploy_workflow_version(
    key: WorkflowKey,
    request: CreateWorkflowVersionRequest,
    db: Database,
) -> dict[str, object]:
    schema_data = request.schema_data.model_dump(mode="json", exclude_none=True)
    try:
        with db.begin() as connection:
            connection.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": key}
            )
            connection.execute(
                text(
                    """
                    UPDATE workflow_versions
                    SET is_active = FALSE
                    WHERE workflow_key = :key
                    """
                ),
                {"key": key},
            )
            next_version = connection.execute(
                text(
                    """
                    SELECT COALESCE(MAX(version), 0) + 1
                    FROM workflow_versions
                    WHERE workflow_key = :key
                    """
                ),
                {"key": key},
            ).scalar_one()
            connection.execute(
                text(
                    """
                    INSERT INTO workflow_versions
                        (workflow_key, version, is_active, schema_data, updated_by, commit_message)
                    VALUES
                        (:key, :version, TRUE, CAST(:schema_data AS JSONB), :updated_by, :commit_message)
                    """
                ),
                {
                    "key": key,
                    "version": next_version,
                    "schema_data": json.dumps(schema_data),
                    "updated_by": request.updated_by,
                    "commit_message": (
                        request.commit_message.strip()
                        if request.commit_message and request.commit_message.strip()
                        else None
                    ),
                },
            )
    except Exception as error:
        raise database_error(
            "Failed to safely deploy new schema version.", error
        ) from error

    return {"success": True, "deployedVersion": next_version}


@app.put(
    "/api/workflow/{key}/rollback/{version}",
    response_model=RollbackWorkflowResponse,
    dependencies=[Depends(require_admin)],
)
# Activates a previously saved workflow version.
def rollback_workflow_version(
    key: WorkflowKey,
    version: Annotated[int, Path(ge=1)],
    db: Database,
) -> dict[str, object]:
    try:
        with db.begin() as connection:
            connection.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": key}
            )
            target_exists = connection.execute(
                text(
                    """
                    SELECT 1
                    FROM workflow_versions
                    WHERE workflow_key = :key AND version = :version
                    """
                ),
                {"key": key, "version": version},
            ).first()
            if target_exists is None:
                raise HTTPException(
                    status_code=404, detail="Target workflow version does not exist."
                )

            connection.execute(
                text(
                    """
                    UPDATE workflow_versions
                    SET is_active = FALSE
                    WHERE workflow_key = :key
                    """
                ),
                {"key": key},
            )
            connection.execute(
                text(
                    """
                    UPDATE workflow_versions
                    SET is_active = TRUE
                    WHERE workflow_key = :key AND version = :version
                    """
                ),
                {"key": key, "version": version},
            )
    except HTTPException:
        raise
    except Exception as error:
        raise database_error("Rollback failed.", error) from error

    return {"success": True, "revertedTo": version}


# Returns all active domain navigation items discovered from domain manifests.
@app.get(
    "/api/domains/navigation",
    response_model=list[DomainManifest],
    summary="Get dynamic domain navigation items",
)
def get_domain_navigation() -> list[DomainManifest]:
    return discover_domain_manifests()


# Records a form submission validated against the active workflow version.
@app.post(
    "/api/workflow/{key}/submission",
    status_code=201,
    summary="Submit data for an active workflow stage",
)
def submit_workflow_data(
    key: WorkflowKey,
    payload: CreateSubmissionRequest,
    db: Database,
) -> dict[str, object]:
    active_data = get_active_workflow(key, db)
    version = int(active_data["version"])
    json_data = json.dumps(payload.data)

    try:
        with db.begin() as connection:
            # Ensure table exists
            connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS form_submissions (
                        id SERIAL PRIMARY KEY,
                        workflow_key VARCHAR(50) NOT NULL,
                        version INT NOT NULL,
                        data JSONB NOT NULL,
                        submitted_by VARCHAR(100),
                        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )
            )
            result = connection.execute(
                text(
                    """
                    INSERT INTO form_submissions (workflow_key, version, data, submitted_by)
                    VALUES (:key, :version, CAST(:data AS jsonb), :submitted_by)
                    RETURNING id
                    """
                ),
                {
                    "key": key,
                    "version": version,
                    "data": json_data,
                    "submitted_by": payload.submitted_by,
                },
            )
            sub_id = result.scalar_one()
    except Exception as error:
        raise database_error("Failed to store submission.", error) from error

    return {"success": True, "id": sub_id, "version": version}


# Dynamically generates metrics and table views projected against the active schema definition in the database.
@app.get(
    "/api/reporting/{key}",
    response_model=DynamicReportResponse,
    summary="Get dynamic reporting projected against the active version",
)
def get_workflow_report(
    key: WorkflowKey,
    db: Database,
) -> DynamicReportResponse:
    # If the user selects the general reporting domain, default to reporting across opportunities
    target_key = "deal_opportunities" if key == "deal_reporting" else key

    active_info = get_active_workflow(target_key, db)
    active_schema = active_info.get("schema_data", {})
    active_version = int(active_info.get("version", 1))

    submissions: list[dict[str, object]] = []
    try:
        with db.connect() as connection:
            table_check = connection.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = 'form_submissions'
                    );
                    """
                )
            ).scalar()

            if table_check:
                rows = (
                    connection.execute(
                        text(
                            """
                            SELECT id, workflow_key, version, data, submitted_by, created_at
                            FROM form_submissions
                            WHERE workflow_key = :key
                            ORDER BY id DESC
                            LIMIT 100
                            """
                        ),
                        {"key": target_key},
                    )
                    .mappings()
                    .all()
                )
                submissions = [dict(row) for row in rows]
    except Exception as error:
        raise database_error("Error reading submissions for reporting.", error) from error

    return generate_dynamic_report(
        workflow_key=key,
        active_schema=active_schema,
        active_version=active_version,
        submissions=submissions,
    )


