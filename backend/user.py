from sqlmodel import select

from backend.models import UserInDB
from backend.database import SessionDependancy


def get_user(session: SessionDependancy, username: str | None = None):
    user = session.exec(select(UserInDB).where(UserInDB.username == username)).first()
    if user:
        user_dict = user.model_dump()
        return UserInDB(**user_dict)
