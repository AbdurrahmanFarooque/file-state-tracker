from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from sqlmodel import select

from models import CaseFile, FileState
from database import create_db_and_tables, populate_filestate, SessionDependancy


app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    populate_filestate()


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.post("/case_files/")
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
    db_case_file = CaseFile(cnr=cnr, state_id=file_state_id)
    session.add(db_case_file)
    session.commit()
    session.refresh(db_case_file)

    return {"message": "Case file uploaded successfully", "case_file": db_case_file}


@app.get("/case_files/")
def list_case_files(session: SessionDependancy):
    case_files = session.exec(select(CaseFile)).all()
    return {"case_files": case_files}


@app.get("/case_files/{cnr}")
def read_case_file_state(cnr: int, session: SessionDependancy):
    case_file = session.get(CaseFile, cnr)
    if not case_file:
        raise HTTPException(status_code=404, detail=f"Case file with CNR '{cnr}' not found.")
    case_file_state = session.get(FileState, case_file.state_id)
    return {"case_file": case_file, "state": case_file_state}


@app.patch("/case_files/{cnr}")
def update_case_file_state(cnr: int, state: str, session: SessionDependancy):
    case_file = session.get(CaseFile, cnr)
    if not case_file:
        raise HTTPException(status_code=404, detail=f"Case file with CNR '{cnr}' not found.")

    # Check if the new state exists
    file_state_exists = session.exec(select(FileState).where(FileState.label == state)).first() is not None
    if not file_state_exists:
        raise HTTPException(status_code=400, detail=f"File state '{state}' does not exist.")
    file_state_id = session.exec(select(FileState.id).where(FileState.label == state)).one()

    case_file.state_id = file_state_id
    session.add(case_file)
    session.commit()
    session.refresh(case_file)

    return {"message": "Case file state updated successfully", "case_file": case_file}


@app.delete("/case_files/{cnr}")
def delete_case_file(cnr: int, session: SessionDependancy):
    case_file = session.get(CaseFile, cnr)
    if not case_file:
        raise HTTPException(status_code=404, detail=f"Case file with CNR '{cnr}' not found.")

    session.delete(case_file)
    session.commit()

    return {"message": "Case file delete successfully", "case_file": case_file}