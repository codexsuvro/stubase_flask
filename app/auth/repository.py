
from uuid import UUID
from sqlalchemy import select
from app.extensions import db
from app.models.user import User


def get_user_by_email(email: str) -> User | None:
    """Fetch a user by email address."""
    statement = select(User).where(User.email == email)
    return db.session.scalar(statement)


def get_user_by_id(user_id: str | UUID) -> User | None:
    """Fetch a user using the user's UUID primary key."""
    try:
        parsed_user_id = (
            user_id if isinstance(user_id, UUID) else UUID(user_id)
        )
    except (ValueError, TypeError, AttributeError):
        return None

    return db.session.get(User, parsed_user_id)


def save_user(user: User) -> User:
    """Persist a user and return the saved instance."""
    db.session.add(user)
    db.session.commit()
    return user


def update_user(user: User) -> User:
    """Persist changes made to an existing user."""
    db.session.add(user)
    db.session.commit()
    return user
