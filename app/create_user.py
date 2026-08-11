"""Create a password account without enabling public registration."""

import argparse
import asyncio
import getpass

from pydantic import ValidationError

from app.db.session import AsyncSessionLocal
from app.models.auth import SignUpRequest
from app.services import auth_service


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--display-name")
    return parser.parse_args()


async def _create_user(payload: SignUpRequest) -> None:
    async with AsyncSessionLocal() as db:
        user = await auth_service.create_password_user(
            db,
            username=payload.username,
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
        )
    print(f"Created user {user.username!r} ({user.id}).")


def main() -> int:
    args = _parse_args()
    password = getpass.getpass("Password (12 characters minimum): ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        print("Passwords do not match.")
        return 2

    try:
        payload = SignUpRequest(
            username=args.username,
            email=args.email,
            display_name=args.display_name,
            password=password,
        )
        asyncio.run(_create_user(payload))
    except ValidationError as exc:
        print(exc)
        return 2
    except auth_service.DuplicateAccountError as exc:
        print(exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
