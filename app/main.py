from datetime import timedelta
from typing import Annotated

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import select
from pwdlib import PasswordHash

from app.models import CaseFile, FileState, User, UserInDB, Token
from app.database import create_db_and_tables, populate_filestate, SessionDependancy
from app.auth import authenticate_user, create_access_token, get_current_active_user, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES


password_hash = PasswordHash.recommended()

DUMMY_HASH = password_hash.hash("dummypassword")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    # populate_filestate()


@app.post("/api/auth/login")
def login_for_access_token(session: SessionDependancy, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")


@app.post("/api/auth/register")
def register_new_user(session: SessionDependancy, username: str, full_name: str, password: str, email: str, disabled: bool = False):
    db_user = UserInDB(username=username, full_name=full_name, hashed_password=get_password_hash(password), email=email, disabled=disabled)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return {"message": "User added successfully", "cred": {"id": db_user.user_id, "username": db_user.username, "password": db_user.hashed_password}}


@app.get("/users/me")
def read_user_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user


@app.get("/users/me/items")
def read_own_items(current_user: Annotated[User, Depends(get_current_active_user)]):
    return {"item_id": "Foo", "owner": current_user.username}


# Upload a new case file
@app.post("/api/case_files/{cnr}")
def upload_case_file(cnr: int, state: str, session: SessionDependancy):
    # Check if the case file already exists
    case_file_exists = session.get(CaseFile, cnr) is not None
    if case_file_exists:
        raise HTTPException(status_code=400, detail=f"Case file with CNR '{cnr}' already exists.")
    
    # Check if the state exists
    file_state_exists = session.exec(select(FileState).where(FileState.label == state)).first() is not None
    if not file_state_exists:
        raise HTTPException(status_code=400, detail=f"File state '{state}' does not exist.")
    file_state_id = session.exec(select(FileState.id).where(FileState.label == state)).one()

    # Create a new case file
    db_case_file = CaseFile(cnr=cnr, file_state_id=file_state_id)
    session.add(db_case_file)
    session.commit()
    session.refresh(db_case_file)

    return {"message": "Case file uploaded successfully", "case_file": {"cnr": db_case_file.cnr, "state": state}}


# Read all case files
@app.get("/api/case_files/")
def list_case_files(session: SessionDependancy, token: Annotated[str, Depends(oauth2_scheme)]):
    case_files = session.exec(select(CaseFile)).all()
    return {"case_files": [{"cnr": case_file.cnr, "state":case_file.file_state.label} for case_file in case_files]}


# Read a specific case file
@app.get("/api/case_files/{cnr}")
def read_case_file_state(cnr: int, session: SessionDependancy):
    case_file = session.get(CaseFile, cnr)
    if not case_file:
        raise HTTPException(status_code=404, detail=f"Case file with CNR '{cnr}' not found.")
    return {"case_file": {"cnr": case_file.cnr, "state": case_file.file_state.label}}


# Update the state of a case file
@app.patch("/api/case_files/{cnr}")
def update_case_file_state(cnr: int, state: str, session: SessionDependancy):
    case_file = session.get(CaseFile, cnr)
    if not case_file:
        raise HTTPException(status_code=404, detail=f"Case file with CNR '{cnr}' not found.")

    # Check if the new state exists
    file_state_exists = session.exec(select(FileState).where(FileState.label == state)).first() is not None
    if not file_state_exists:
        raise HTTPException(status_code=400, detail=f"File state '{state}' does not exist.")
    file_state_id = session.exec(select(FileState.id).where(FileState.label == state)).one()

    case_file.file_state_id = file_state_id
    session.add(case_file)
    session.commit()
    session.refresh(case_file)

    return {"message": "Case file state updated successfully", "case_file": {"cnr": case_file.cnr, "state": case_file.file_state.label}}


# Delete a case file
@app.delete("/api/case_files/{cnr}")
def delete_case_file(cnr: int, session: SessionDependancy):
    case_file = session.get(CaseFile, cnr)
    if not case_file:
        raise HTTPException(status_code=404, detail=f"Case file with CNR '{cnr}' not found.")

    case_file_cnr = case_file.cnr
    case_file_state = case_file.file_state.label

    session.delete(case_file)
    session.commit()

    return {"message": "Case file deleted successfully", "case_file": {"cnr": case_file_cnr, "state": case_file_state}}
