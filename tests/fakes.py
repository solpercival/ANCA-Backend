"""Shared test doubles."""

from rag_engine.retrieval.interfaces import Alarm

FB_0002 = Alarm(
    code="am.fb.0002",
    title="EtherCAT slave lost",
    domain="Fieldbus",
    severity_score=900,
    severity_category="error",
    alarm_text="EtherCAT slave 3 stopped responding.",
    data_fields={},
)


class FakeAlarmStore:
    """In-memory catalogue; unknown codes return None like the real store."""

    def __init__(self, *alarms: Alarm):
        self._alarms = {a.code: a for a in (alarms or (FB_0002,))}

    async def get_alarm(self, code: str) -> Alarm | None:
        return self._alarms.get(code)


class FakePreprocessor:
    """Passes the query through unchanged and stores no conversation context."""

    async def process_prompt(self, raw_query, conversation_id, effort):
        return raw_query

    def store_context(self, conversation_id, query, response, alarm):
        return
