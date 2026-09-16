"""
Request and response models for the /auth endpoints.

These define the JSON contract the frontend sees. Internal records such as
interfaces.User are converted into these models before being returned, so
fields like the password hash never reach a response.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from rag_engine.auth.tiers import Tier
from rag_engine.auth.service import normalize_username


class TokenResponse(BaseModel):
    """
    Body returned by login and refresh, following the OAuth2 token response shape.

    The refresh token is not included; it is set as an HttpOnly cookie instead.
    """

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class UserOut(BaseModel):
    """Public view of an account, returned by GET /auth/me."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    tier: Tier
