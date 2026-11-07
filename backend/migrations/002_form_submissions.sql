CREATE TABLE IF NOT EXISTS form_submissions (
    id SERIAL PRIMARY KEY,
    workflow_key VARCHAR(50) NOT NULL,
    version INT NOT NULL CHECK (version > 0),
    data JSONB NOT NULL,
    submitted_by VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_submissions_key_version
    ON form_submissions (workflow_key, version);

