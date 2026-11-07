CREATE TABLE IF NOT EXISTS workflow_versions (
    id SERIAL PRIMARY KEY,
    workflow_key VARCHAR(50) NOT NULL,
    version INT NOT NULL CHECK (version > 0),
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    schema_data JSONB NOT NULL,
    updated_by VARCHAR(100) NOT NULL,
    commit_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (workflow_key, version)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_active_workflow
    ON workflow_versions (workflow_key)
    WHERE is_active = TRUE;
