"""Alarm catalogue lookup: maps an alarm code to its catalogue record.

The catalogue is seeded from the starter-kit alarms.sample.json by
`python -m ingestion.seed_alarms` (also run as part of `make ingest`).
"""

import asyncio

from rag_engine.config import get_settings
from rag_engine.retrieval.interfaces import Alarm
from rag_engine.stores.db import get_db_conn


class PostgresAlarmStore:
    async def get_alarm(self, code: str) -> Alarm | None:
        """Return the catalogue record for `code`, or None if it isn't catalogued."""
        parts = code.split(get_settings().alarm_delim)
        if len(parts) != 3:
            return None
        # sync psycopg pool: query in a worker thread so the event loop isn't blocked
        row = await asyncio.to_thread(self._fetch_alarm_row, *parts)

        if not row:
            return None
        return Alarm(
            code=code,
            title=row["title"],
            domain=row["domain"],
            severity_score=row["severity_score"],
            severity_category=row["severity_category"],
            alarm_text=row["alarm_text"],
            data_fields=row["data_fields"] or {},  # JSONB is decoded by psycopg
        )

    @staticmethod
    def _fetch_alarm_row(origin: str, module: str, sequence: str) -> dict | None:
        """Blocking catalogue query for get_alarm; runs in a worker thread.

        `code` is "<origin>.<module>.<sequence>" (e.g. am.fb.0002): the module part
        matches alarm_module.code, the other two match alarm_code columns.
        """
        with get_db_conn() as conn:
            return conn.execute(
                """
                SELECT ac.title, ac.severity_score, ac.severity_category,
                       ac.alarm_text, ac.data_fields, am.title AS domain
                FROM alarm_code ac
                JOIN alarm_module am ON am.id = ac.module
                WHERE ac.origin = %s AND am.code = %s AND ac.alarm_sequence = %s
                LIMIT 1;
                """,
                (origin, module, sequence),
            ).fetchone()
