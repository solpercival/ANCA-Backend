"""Seed the alarm catalogue (alarm_module + alarm_code) from an alarms JSON file.

Idempotent: rows are upserted, so re-running refreshes titles/text in place.

    python -m ingestion.seed_alarms [path/to/alarms.json]
"""
import json
import sys
from pathlib import Path

DEFAULT_ALARMS_PATH = "docs/docs-proto/starter-kit/alarms/alarms.sample.json"


def load_alarms(path: str = DEFAULT_ALARMS_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def seed(path: str = DEFAULT_ALARMS_PATH) -> int:  # pragma: no cover - integration
    # lazy: ingestion.indexers pulls in the model/tokenizer stack
    from ingestion.indexers import populate_alarms

    alarms_json = load_alarms(path)
    populate_alarms(alarms_json)
    return len(alarms_json["alarms"])


if __name__ == "__main__":  # pragma: no cover
    n = seed(*sys.argv[1:2])
    print(f"seeded {n} alarm codes")
