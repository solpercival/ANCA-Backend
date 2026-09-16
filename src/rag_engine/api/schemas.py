"""Request/response contracts for the resolve + chat API."""
from pydantic import BaseModel, Field

from rag_engine.auth.tiers import Tier


class Env(BaseModel):
    versions: dict[str, str] = Field(default_factory=dict)
    machine_variant: str | None = None


class ResolveRequest(BaseModel):
    code: str = Field(..., examples=["am.fb.0002"])
    env: Env = Field(default_factory=Env)
    query: str | None = Field(None, description="Optional free-text symptom")


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
    conversation_id: str
    message: str


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    citations: list[Citation] = Field(default_factory=list)
