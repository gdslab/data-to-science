import argparse
import logging
import sys
import warnings

from sqlalchemy import func, select

warnings.filterwarnings("ignore", message="relationship .* will copy column")

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_superuser(email: str, password: str, first_name: str, last_name: str) -> None:
    with SessionLocal() as session:
        try:
            with session.begin():
                existing = session.scalar(
                    select(User).where(func.lower(User.email) == email.lower())
                )
                if existing:
                    logger.error(f"User with email '{email}' already exists.")
                    sys.exit(1)

                user = User(
                    email=email,
                    hashed_password=get_password_hash(password),
                    first_name=first_name,
                    last_name=last_name,
                    is_superuser=True,
                    is_approved=True,
                    is_email_confirmed=True,
                )
                session.add(user)
        except SystemExit:
            raise
        except Exception as e:
            logger.error(f"Failed to create superuser: {e}")
            sys.exit(1)

    logger.info(f"Superuser '{email}' created successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a D2S superuser")
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument("--first-name", required=True, help="First name")
    parser.add_argument("--last-name", required=True, help="Last name")
    parser.add_argument("--password", required=True, help="Password")

    args = parser.parse_args()

    create_superuser(
        email=args.email,
        password=args.password,
        first_name=args.first_name,
        last_name=args.last_name,
    )


if __name__ == "__main__":
    main()
