from sqlmodel import select

from app.backend.models import User
from app.backend.database import SessionDependancy


def get_user(session: SessionDependancy, username: str | None = None):
    return session.exec(select(User).where(User.username == username)).first()