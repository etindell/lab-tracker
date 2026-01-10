"""CLI commands for Lab Tracker."""

import argparse
import sys

from app.config import get_settings
from app.database.session import SessionLocal
from app.services.user import UserService
from app.services.password import generate_temp_password


def create_admin(email: str, name: str) -> None:
    """Create an admin user.

    Args:
        email: Admin email address.
        name: Admin display name.
    """
    db = SessionLocal()
    try:
        user_service = UserService(db)

        # Check if user already exists
        existing = user_service.get_by_email(email)
        if existing:
            print(f"Error: User with email {email} already exists")
            sys.exit(1)

        # Generate password
        temp_password = generate_temp_password()

        # Create user
        user = user_service.create_user(
            email=email,
            name=name,
            password=temp_password,
            is_admin=True,
        )

        print(f"Admin user created successfully!")
        print(f"  Email: {user.email}")
        print(f"  Name: {user.name}")
        print(f"  Temporary Password: {temp_password}")
        print()
        print("Please change this password after first login.")

    finally:
        db.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Lab Tracker CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # create-admin command
    admin_parser = subparsers.add_parser(
        "create-admin",
        help="Create an admin user",
    )
    admin_parser.add_argument(
        "--email",
        required=True,
        help="Admin email address",
    )
    admin_parser.add_argument(
        "--name",
        required=True,
        help="Admin display name",
    )

    args = parser.parse_args()

    if args.command == "create-admin":
        create_admin(args.email, args.name)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
