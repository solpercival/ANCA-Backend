"""
Account tiers, the authenticated principal, and tier capability checks.

A tier is the access level attached to every account and carried in its access
token. Routes decide what a caller may see by calling the capability functions
here rather than comparing tiers inline, so each rule is defined in one place.
"""

from dataclasses import dataclass
from enum import StrEnum


class Tier(StrEnum):
    """
    Access level assigned to an account.

    The value is stored on the user record and in the access token's `tier`
    claim. Renaming a value invalidates every access token already issued with it.
    """

    operator = "operator"
    technician = "technician"
    partner = "partner"


@dataclass(frozen=True)
class Principal:
    """
    The caller identified by a verified access token.

    Built from token claims alone, so `tier` is the tier at the moment the token
    was issued and can be up to one access-token lifetime out of date. Depend on
    `current_user` instead when the live account record is needed.

    Attributes:
        subject: The user's ID as a string (the JWT `sub` claim).
        tier: The account tier the token was issued for.
    """

    subject: str
    tier: Tier


def can_use_chat(tier: Tier) -> bool:
    """Return whether the tier may use the chat endpoint."""
    return (tier is Tier.technician) or (tier is Tier.partner)


def can_view_likely_causes(tier: Tier) -> bool:
    """Return whether the tier may see the likely causes behind an alarm."""
    return (tier is Tier.technician) or (tier is Tier.partner)
