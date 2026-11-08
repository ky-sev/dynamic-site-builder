import json
import logging
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, text

from settings import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

INTAKE_SAMPLES = [
    {"customerName": "Acme Holdings", "dealName": "Project Falcon Acquisition", "dealType": "Acquisition"},
    {"customerName": "Northwind Traders", "dealName": "Global Logistics Partnership", "dealType": "Partnership"},
    {"customerName": "Stark Industries", "dealName": "Energy Infrastructure Renewal", "dealType": "Renewal"},
    {"customerName": "Wayne Enterprises", "dealName": "Defense System Partnership", "dealType": "Partnership"},
    {"customerName": "Cyberdyne Systems", "dealName": "AI Compute Cluster Deal", "dealType": "Acquisition"},
    {"customerName": "Initech Corp", "dealName": "TPS Automation Renewal", "dealType": "Renewal"},
    {"customerName": "Umbrella Corp", "dealName": "BioTech Facility Acquisition", "dealType": "Acquisition"},
    {"customerName": "Massive Dynamic", "dealName": "Quantum Research Partnership", "dealType": "Partnership"},
    {"customerName": "Hooli", "dealName": "Compression Platform Acquisition", "dealType": "Acquisition"},
    {"customerName": "Pied Piper", "dealName": "Decentralized Network Renewal", "dealType": "Renewal"},
]

OPPORTUNITY_SAMPLES = [
    {"fundingReceived": True, "contractSigned": True},
    {"fundingReceived": True, "contractSigned": False},
    {"fundingReceived": False, "contractSigned": False},
    {"fundingReceived": True, "contractSigned": True},
    {"fundingReceived": True, "contractSigned": True},
    {"fundingReceived": False, "contractSigned": False},
    {"fundingReceived": True, "contractSigned": False},
    {"fundingReceived": True, "contractSigned": True},
    {"fundingReceived": True, "contractSigned": True},
    {"fundingReceived": False, "contractSigned": False},
]

USERS = ["alex.morgan@example.com", "taylor.reed@example.com", "jordan.lee@example.com", "sam.rivera@example.com"]


def seed_database(num_records: int = 10) -> None:
    try:
        db_url = settings.sqlalchemy_database_url()
    except Exception as err:
        logger.error(f"Configuration error: {err}")
        return

    connect_args = {"connect_timeout": 5}
    engine = create_engine(db_url, connect_args=connect_args)

    logger.info(f"Connecting to database at {engine.url.host}:{engine.url.port or 5432}...")

    try:
        with engine.begin() as connection:
            # 1. Ensure table exists
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
                    CREATE INDEX IF NOT EXISTS idx_submissions_key_version
                        ON form_submissions (workflow_key, version);
                    """
                )
            )

            now = datetime.now(timezone.utc)

            # 2. Seed Intakes (deal_intake)
            logger.info(f"Seeding {num_records} Intake records...")
            for i in range(num_records):
                sample = INTAKE_SAMPLES[i % len(INTAKE_SAMPLES)]
                submitted_by = random.choice(USERS)
                created_at = now - timedelta(days=random.randint(0, 14), hours=random.randint(1, 23))

                connection.execute(
                    text(
                        """
                        INSERT INTO form_submissions (workflow_key, version, data, submitted_by, created_at)
                        VALUES (:key, :version, CAST(:data AS jsonb), :submitted_by, :created_at)
                        """
                    ),
                    {
                        "key": "deal_intake",
                        "version": 1,
                        "data": json.dumps(sample),
                        "submitted_by": submitted_by,
                        "created_at": created_at,
                    },
                )

            # 3. Seed Opportunities (deal_opportunities)
            logger.info(f"Seeding {num_records} Opportunity records...")
            for i in range(num_records):
                sample = OPPORTUNITY_SAMPLES[i % len(OPPORTUNITY_SAMPLES)]
                submitted_by = random.choice(USERS)
                created_at = now - timedelta(days=random.randint(0, 14), hours=random.randint(1, 23))

                connection.execute(
                    text(
                        """
                        INSERT INTO form_submissions (workflow_key, version, data, submitted_by, created_at)
                        VALUES (:key, :version, CAST(:data AS jsonb), :submitted_by, :created_at)
                        """
                    ),
                    {
                        "key": "deal_opportunities",
                        "version": 1,
                        "data": json.dumps(sample),
                        "submitted_by": submitted_by,
                        "created_at": created_at,
                    },
                )

        logger.info("Successfully populated test submissions for 'deal_intake' and 'deal_opportunities'!")
    except Exception as err:
        logger.error(
            f"Could not connect to PostgreSQL: {err}\n"
            "If using Docker Compose, ensure the database port is published (e.g. '127.0.0.1:5432:5432') "
            "or run the seed script directly inside the container:\n"
            "  docker compose exec api python seed_data.py"
        )


if __name__ == "__main__":
    seed_database()
