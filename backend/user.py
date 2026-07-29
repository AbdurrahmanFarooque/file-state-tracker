from sqlmodel import select

from backend.models import User
from backend.database import SessionDependancy


def get_user(session: SessionDependancy, username: str | None = None):
    user = session.exec(select(User).where(User.username == username)).first()
    if user:
        user_dict = user.model_dump()
        return User(**user_dict)
