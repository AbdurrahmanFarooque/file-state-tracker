from fastapi import APIRouter

from app.backend.database import SessionDependancy
from app.backend.dependencies import CurrentActiveUserDependency
from app.backend.core.security import get_password_hash
from app.backend.models import (
    User,
    UserBase,
    UserCreate,
    UserUpdate,
    UserPublic,
)

router = APIRouter(
    prefix="/api/users",
    tags=["users"]
)


@router.post("/auth/register")
def register_new_user(session: SessionDependancy, user: UserCreate) -> UserBase:
    hashed_password = get_password_hash(user.password)
    user_data = user.model_dump(exclude={"password"})

    db_user = User(**user_data, hashed_password=hashed_password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return user


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentActiveUserDependency):
    print(current_user)
    return current_user


@router.get("/me/items")
def read_own_items(current_user: CurrentActiveUserDependency):
    return {"item_id": "Foo", "owner": current_user.full_name}


@router.patch("/me")
def update_profile(user_update: UserUpdate, current_user: CurrentActiveUserDependency, session: SessionDependancy):
    current_user.full_name = user_update.full_name
    current_user.email = user_update.email  

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return {"message": "Profile updated successfully", "updated profile": current_user}


@router.delete("/me")
def disable_profile(current_user: CurrentActiveUserDependency, session: SessionDependancy):
    current_user.disabled = True

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return {"message": "Profile disabled", "disabled": current_user.disabled}