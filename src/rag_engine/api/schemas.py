"""Request/response contracts for the resolve + chat API."""
from pydantic import BaseModel, Field

from rag_engine.auth.tiers import Tier

# TODO: confirm exact alarm-code format with the docs team; starter-kit data
# regex should match the known examples 
ALARM_CODE_PATTERN = r"^[a-z]{2,4}\.[a-z]{2,6}\.\d{4}$"


class Env(BaseModel):
    versions: dict[str, str] = Field(default_factory=dict)
    machine_variant: str | None = None


class ResolveRequest(BaseModel):
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
    source: str
    chunk_id: str


class ResolveResponse(BaseModel):
    code: str
    steps: list[str]
    likely_causes: list[str] = Field(default_factory=list)  # technician+ only
    citations: list[Citation] = Field(default_factory=list)
    tier: Tier
    ai_chat_available: bool = False # whether the caller may use /api/v1/chat
    confidence: float = 0.0


class ChatRequest(BaseModel):
    conversation_id: str = Field(..., min_length=1, max_length=128)
    message: str = Field(..., min_length=1, max_length=4096)


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    citations: list[Citation] = Field(default_factory=list)
