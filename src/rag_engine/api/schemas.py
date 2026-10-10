"""Request/response contracts for the resolve + chat API."""
from typing import Literal

from pydantic import BaseModel, Field

from rag_engine.auth.tiers import Tier

DocCoverage = Literal["full", "partial", "none"]

# TODO: confirm exact alarm-code format with the docs team; starter-kit data
# regex should match the known examples 
ALARM_CODE_PATTERN = r"^[a-z]{2,4}\.[a-z]{2,6}\.\d{4}$"


class Env(BaseModel):
    """The caller's machine context; narrows retrieval to matching documentation."""
    versions: dict[str, str] = Field(default_factory=dict)  # component -> version
    machine_variant: str | None = None


class ResolveRequest(BaseModel):
    """Body of POST /api/v2/resolve."""
    code: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=ALARM_CODE_PATTERN,
        examples=["am.fb.0002"],
    )
    env: Env = Field(default_factory=Env)
    query: str | None = Field(
        None,
        max_length=1000,
        description="Optional free-text symptom",
    )


class Citation(BaseModel):
    """A documentation chunk the answer was built from."""
    source: str  # document path
    chunk_id: str


class ResolveResponse(BaseModel):
    """Guidance for one alarm. Tier rules are already applied (see api/routes.py)."""
    code: str
    # alarm header, rendered from the alarm catalogue (identifies the alarm only;
    # never a source of guidance -- that comes from the docs via steps/causes)
    title: str | None = None
    domain: str | None = None
    severity: int | None = Field(None, description="1-1000")
    severity_category: str | None = Field(None, examples=["Error"])
    steps: list[str] = Field(
        ..., description="Doc-grounded explanation/guidance, one point per element"
    )
    doc_coverage: DocCoverage = Field(
        "none",
        description=(
            "full: the docs give explicit steps that resolve the alarm; partial: the "
            "docs explain the alarm/behaviour but no complete fix; none: the docs "
            "don't cover it (same scale as reference-answers.json)"
        ),
    )
    likely_causes: list[str] = Field(
        default_factory=list,
        description="Up to 3 likely causes; technician/partner only, always [] for operators",
    )
    citations: list[Citation] = Field(default_factory=list)
    tier: Tier
    ai_chat_available: bool = False  # whether the caller may use /api/v2/chat
    escalation_suggested: bool = Field(
        False,
        description="Whether the caller should be offered escalation to a technician",
    )
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description=(
            "Kept for the interface contract; derived from doc_coverage "
            "(full 0.9, partial 0.5, none 0.0), not a model probability"
        ),
    )


class ChatRequest(BaseModel):
    """Body of POST /api/v2/chat. Reuse conversation_id to continue a conversation."""
    conversation_id: str = Field(..., min_length=1, max_length=128)
    message: str = Field(..., min_length=1, max_length=4096)


class ChatResponse(BaseModel):
    """The assistant's reply and the documentation it drew on."""
    conversation_id: str
    reply: str
    citations: list[Citation] = Field(default_factory=list)
