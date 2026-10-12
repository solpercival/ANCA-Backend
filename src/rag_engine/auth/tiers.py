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


class DocAudience(StrEnum):
    """
    A documentation set with its own audience, named by its folder in the docs tree.

    A chunk belongs to an audience when its document path (document_source)
    contains `path_fragment`, e.g. .../docs/user-guide/troubleshoot/x.md.
    """

    user_guide = "user-guide"
    part_programmers_reference = "part-programmers-reference"

    @property
    def path_fragment(self) -> str:
        """The folder as it appears inside a document path."""
        return f"/{self.value}/"


# Client rule: the User Guide is for technician and partner only; the Part
# Programmer's Reference is for every tier. None = unrestricted (every document,
# including any outside the audience folders).
_DOC_AUDIENCES: dict[Tier, frozenset[DocAudience] | None] = {
    Tier.operator: frozenset({DocAudience.part_programmers_reference}),
    Tier.technician: None,
    Tier.partner: None,
}


def allowed_doc_audiences(tier: Tier) -> frozenset[DocAudience] | None:
    """
    Return the documentation sets the tier's answers may draw on.

    None means unrestricted. Otherwise retrieval must only return chunks whose
    document lies in one of the returned audiences' folders.
    """
    return _DOC_AUDIENCES[tier]


def can_use_chat(tier: Tier) -> bool:
    """Return whether the tier may use the chat endpoint."""
    return (tier is Tier.technician) or (tier is Tier.partner)


def can_view_likely_causes(tier: Tier) -> bool:
    """Return whether the tier may see the likely causes behind an alarm."""
    return (tier is Tier.technician) or (tier is Tier.partner)
