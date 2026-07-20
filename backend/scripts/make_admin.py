"""Grants (or revokes) a user's admin flag.

Run from the backend/ directory:

    python scripts/make_admin.py <username>
    python scripts/make_admin.py <username> --revoke

This is deliberately a database-side script rather than an API endpoint:
it sidesteps the bootstrap problem (who admins the first admin?) and
keeps privilege escalation entirely out of the API surface.
"""

import argparse
import sys
from pathlib import Path

# Make `import app...` work when invoked as `python scripts/make_admin.py`
# (Python puts the script's own directory on sys.path, not the cwd).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session, select  # noqa: E402

from app.database import engine  # noqa: E402
from app.models import User  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Grant or revoke the admin flag.")
    parser.add_argument("username")
    parser.add_argument("--revoke", action="store_true", help="remove the admin flag instead")
    args = parser.parse_args()

    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == args.username)).first()
        if user is None:
            print(f"No user named {args.username!r}.", file=sys.stderr)
            return 1
        user.is_admin = not args.revoke
        session.add(user)
        session.commit()
        state = "revoked from" if args.revoke else "granted to"
        print(f"Admin {state} {args.username!r}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
