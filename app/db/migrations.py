from __future__ import annotations

from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine


MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "sql" / "migrations"


def _ensure_migrations_table(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )


def _fetch_applied_versions(engine: Engine) -> set[str]:
    with engine.begin() as connection:
        rows = connection.execute(text("SELECT version FROM schema_migrations")).fetchall()
    return {row[0] for row in rows}


def run_migrations(engine: Engine) -> list[str]:
    _ensure_migrations_table(engine)

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        return []

    applied_versions = _fetch_applied_versions(engine)
    executed_versions: list[str] = []

    for migration_file in migration_files:
        version = migration_file.stem
        if version in applied_versions:
            continue

        sql = migration_file.read_text(encoding="utf-8").strip()
        if not sql:
            continue

        with engine.begin() as connection:
            for statement in [part.strip() for part in sql.split(";") if part.strip()]:
                connection.execute(text(statement))
            connection.execute(
                text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                {"version": version},
            )

        executed_versions.append(version)

    return executed_versions
