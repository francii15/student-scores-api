import os
from pathlib import Path
import subprocess
import sys

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import URL, create_engine, inspect

import models
from database import Base


def test_migrations_create_fresh_database(tmp_path):
    project_directory = Path(__file__).resolve().parent
    database_path = tmp_path / "migration_test.db"

    environment = os.environ.copy()
    environment["DATABASE_PATH"] = str(database_path)

    # Run migrations in a separate Python process.
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "upgrade",
            "head",
        ],
        cwd=project_directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, (
        result.stdout + result.stderr
    )

    test_engine = create_engine(
        URL.create(
            "sqlite",
            database=str(database_path),
        )
    )

    try:
        inspector = inspect(test_engine)

        assert {
            "students",
            "users",
            "refresh_sessions",
            "alembic_version",
        }.issubset(inspector.get_table_names())

        user_columns = {
            column["name"]
            for column in inspector.get_columns("users")
        }
        assert "role" in user_columns

        # Compare the migrated database with our models.
        with test_engine.connect() as connection:
            context = MigrationContext.configure(connection)
            differences = compare_metadata(
                context,
                Base.metadata,
            )

            assert differences == []
    finally:
        test_engine.dispose()