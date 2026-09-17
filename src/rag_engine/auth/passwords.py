"""
Password hashing and verification with Argon2id.

Hashing is deliberately slow and CPU-bound, so every call runs in the threadpool
to keep the event loop free for RAG requests. Verification also reports when a
stored hash uses outdated parameters so the caller can save a rehashed value.
"""

from functools import cache

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from starlette.concurrency import run_in_threadpool

# OWASP (Open Worldwide Application Security Project) baseline for Argon2id.
# Raising these rehashes each user on their next login.
_hasher = PasswordHash((Argon2Hasher(time_cost=2, memory_cost=19456, parallelism=1),))


@cache
def _dummy_hash() -> str:
    """
    Return a hash to verify against when the user does not exist.

    Computed once on first use, so the first failed login for an unknown user
    pays for one extra hash.
    """
    return _hasher.hash("timing-equaliser")


async def hash_password(password: str) -> str:
    """
    Hash a plaintext password for storage.

    Returns:
        An encoded Argon2id hash that includes its salt and parameters.
    """
    return await run_in_threadpool(_hasher.hash, password)


async def verify_password(password: str, password_hash: str) -> tuple[bool, str | None]:
    """
    Check a plaintext password against a stored hash.

    Pass None as `password_hash` for an unknown user: a dummy hash is still
    verified so response time does not reveal whether the account exists.

    Returns:
        `(valid, upgraded_hash)`. `upgraded_hash` is a new hash to store when
        the password is valid but the stored hash uses outdated parameters;
        otherwise it is None.
    """
    if password_hash is None:
        await run_in_threadpool(lambda: _hasher.verify(password, _dummy_hash()))
        return False, None
    return await run_in_threadpool(_hasher.verify_and_update, password, password_hash)
