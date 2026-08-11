from datetime import timedelta
from enum import Enum
from typing import Annotated

from fastapi import FastAPI, HTTPException, Depends, Form, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import select
from pwdlib import PasswordHash

from backend.models import CaseFile, FileLocation, FileLocationCreate, UserCreate, UserPublic, UserUpdate, User, Token, UserRole
from backend.database import create_db_and_tables, populate_filelocation, SessionDependancy
from backend.auth import authenticate_user, create_access_token, get_current_active_user, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES


password_hash = PasswordHash.recommended()

DUMMY_HASH = password_hash.hash("dummypassword")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    # populate_filelocation()


@app.post("/token")
def login_for_access_token(session: SessionDependancy, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.full_name}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")


@app.post("/api/auth/register")
def register_new_user(session: SessionDependancy, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    user_data = user.model_dump(exclude={"password"})

    db_user = User(**user_data, hashed_password=hashed_password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return {"message": "User added successfully", "cred": {"id": db_user.user_id, "username": db_user.username, "password": db_user.hashed_password}}


@app.get("/api/users/me", response_model=UserPublic)
def read_user_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    # print(current_user)
    return current_user


@app.get("/api/users/me/items")
def read_own_items(current_user: Annotated[User, Depends(get_current_active_user)]):
    return {"item_id": "Foo", "owner": current_user.full_name}


@app.patch("/api/users/me")
def update_profile(user_update: UserUpdate, current_user: Annotated[User, Depends(get_current_active_user)], session: SessionDependancy):
    current_user.full_name = user_update.full_name
    current_user.email = user_update.email  

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return {"message": "Profile updated successfully", "updated profile": current_user}


@app.delete("/api/users/me")
def disable_profile(current_user: Annotated[User, Depends(get_current_active_user)], session: SessionDependancy):
    current_user.disabled = True

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return {"message": "Profile disabled", "disabled": current_user.disabled}


@app.post("/api/locations")
def create_location(location: FileLocationCreate, session: SessionDependancy):
    # Check if the location already exists
    location_exists = session.exec(select(FileLocation).where(FileLocation.name == location.name)).first() is not None
    if location_exists:
        raise HTTPException(status_code=400, detail=f"Location '{location.name}' already exists.")

    # Create new FileLocation
    db_location = FileLocation(name=location.name)
    session.add(db_location)
    session.commit()
    session.refresh(db_location)

    return {"message": "Location added successfully", "location": db_location.name}


# Upload a new case file (remove function?)
@app.post("/api/case_files/{cnr}")
def upload_case_file(cnr: int, location: str, session: SessionDependancy):
    # Check if the case file already exists
    case_file_exists = session.get(CaseFile, cnr) is not None
    if case_file_exists:
        raise HTTPException(status_code=400, detail=f"Case file with CNR '{cnr}' already exists.")
    
    # Check if the location exists
    file_location_exists = session.exec(select(FileLocation).where(FileLocation.name == location)).first() is not None
    if not file_location_exists:
        raise HTTPException(status_code=400, detail=f"File location '{location}' does not exist.")
    file_location_id = session.exec(select(FileLocation.location_id).where(FileLocation.name == location)).one()

    # Create a new case file
    db_case_file = CaseFile(cnr=cnr, location_id=file_location_id)
    session.add(db_case_file)
    session.commit()
    session.refresh(db_case_file)

    return {"message": "Case file uploaded successfully", "case_file": {"cnr": db_case_file.cnr, "location": location}}


# Read all case files
@app.get("/api/case_files/")
def list_case_files(session: SessionDependancy, token: Annotated[str, Depends(oauth2_scheme)]):
    case_files = session.exec(select(CaseFile)).all()
    return {"case_files": [{"cnr": case_file.cnr, "location":case_file.file_location.name} for case_file in case_files]}


# Read a specific case file
@app.get("/api/case_files/{cnr}")
def read_case_file_location(cnr: int, session: SessionDependancy):
    case_file = session.get(CaseFile, cnr)
    if not case_file:
        raise HTTPException(status_code=404, detail=f"Case file with CNR '{cnr}' not found.")
    return {"case_file": {"cnr": case_file.cnr, "location": case_file.file_location.name}}


# Update the location of a case file
@app.patch("/api/case_files/{cnr}")
def update_case_file_location(cnr: int, location: str, session: SessionDependancy):
    case_file = session.get(CaseFile, cnr)
    if not case_file:
        raise HTTPException(status_code=404, detail=f"Case file with CNR '{cnr}' not found.")

    # Check if the new location exists
    file_location_exists = session.exec(select(FileLocation).where(FileLocation.name == location)).first() is not None
    if not file_location_exists:
        raise HTTPException(status_code=400, detail=f"File location '{location}' does not exist.")
    file_location_id = session.exec(select(FileLocation.location_id).where(FileLocation.name == location)).one()

    case_file.location_id = file_location_id
    session.add(case_file)
    session.commit()
    session.refresh(case_file)

    return {"message": "Case file location updated successfully", "case_file": {"cnr": case_file.cnr, "location": case_file.file_location.name}}


# Delete a case file
@app.delete("/api/case_files/{cnr}")
def delete_case_file(cnr: int, session: SessionDependancy):
    case_file = session.get(CaseFile, cnr)
    if not case_file:
        raise HTTPException(status_code=404, detail=f"Case file with CNR '{cnr}' not found.")

    case_file_cnr = case_file.cnr
    case_file_location = case_file.file_location.name

    session.delete(case_file)
    session.commit()

    return {"message": "Case file deleted successfully", "case_file": {"cnr": case_file_cnr, "location": case_file_location}}


# Check 'Body - Nested Models''
@app.patch("api/case_files/")
def send_case_files(case_files: list[CaseFile], session: SessionDependancy):
    return {}