"""Create or update a login account, or deactivate one (run by `make user` /
`make user-disable`; needs the stack's Postgres running).

  python scripts/manage_user.py set <username> <operator|technician|partner>
  python scripts/manage_user.py disable <username>

`set` creates the account, or gives an existing one a new password and tier, and
reactivates it. The password is asked for twice and never echoed; set USER_PASSWORD
instead for a non-interactive run.
"""

import asyncio
import getpass
import os
import sys

from rag_engine.auth import passwords
from rag_engine.auth.service import normalize_username
from rag_engine.auth.tiers import Tier
from rag_engine.auth.user_repository import PostgresUserRepository
from rag_engine.stores.db import init_db_pool

MIN_PASSWORD_LENGTH = 12


def _password() -> str:
    if os.environ.get("USER_PASSWORD"):
        password = os.environ["USER_PASSWORD"]
    else:
        password = getpass.getpass("Password: ")
        if getpass.getpass("Repeat password: ") != password:
            sys.exit("Passwords do not match")
    if len(password) < MIN_PASSWORD_LENGTH:
        sys.exit(f"Use at least {MIN_PASSWORD_LENGTH} characters")
    return password


async def set_user(username: str, tier_name: str) -> None:
    try:
        tier = Tier(tier_name)
    except ValueError:
        sys.exit(f"Unknown tier {tier_name!r}; use one of: {', '.join(t.value for t in Tier)}")
    users = PostgresUserRepository()
    password_hash = await passwords.hash_password(_password())
    existing = await users.get_by_username(username)
    if existing is None:
        if await users.create(username, password_hash, tier) is None:
            sys.exit(f"Could not create {username!r}")
        print(f"Created {username} ({tier.value})")
        return
    await users.update_password_hash(existing.user_id, password_hash)
    await users.update_tier(existing.user_id, tier)
    await users.set_active(existing.user_id, True)
    print(f"Updated {username}: new password, tier {tier.value}, active")


async def disable_user(username: str) -> None:
    users = PostgresUserRepository()
    existing = await users.get_by_username(username)
    if existing is None:
        sys.exit(f"No account {username!r}")
    await users.set_active(existing.user_id, False)
    print(f"Deactivated {username}; it can no longer log in")


def main(argv: list[str]) -> None:
    # stored names are trimmed and lower-case, as login looks them up
    if len(argv) == 3 and argv[0] == "set":
        action = set_user(normalize_username(argv[1]), argv[2])
    elif len(argv) == 2 and argv[0] == "disable":
        action = disable_user(normalize_username(argv[1]))
    else:
        sys.exit(__doc__)
    init_db_pool()
    asyncio.run(action)


if __name__ == "__main__":
    main(sys.argv[1:])
