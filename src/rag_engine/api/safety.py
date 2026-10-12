"""Which alarms are safety-related.

Client rule: for Fatal or safety-related alarms, always tell the user to verify
before acting; for operators, tell them to escalate if unsure. This module holds
only the classification, shared by the two places that act on it:
  orchestrator.py  sets ResolveResponse.safety_note (content, every tier)
  api/routes.py    sets escalation_suggested / escalation_note (tier rule)
"""

from rag_engine.config import get_settings


def is_safety_alarm(severity_category: str | None) -> bool:
    """Whether an alarm of this severity category is in the safety set
    (settings.safety_severity_categories, default {"Fatal"}). Case-insensitive;
    an alarm with no category is not."""
    if not severity_category:
        return False
    categories = {c.strip().lower() for c in get_settings().safety_severity_categories}
    return severity_category.strip().lower() in categories
