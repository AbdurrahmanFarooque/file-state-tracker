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


# Upload a new case file
@app.post("/case_files/{cnr}")
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
@app.get("/case_files/")
def list_case_files(session: SessionDependancy):
    case_files = session.exec(select(CaseFile)).all()
    return {"case_files": [{"cnr": case_file.cnr, "state":case_file.file_state.label} for case_file in case_files]}


# Read a specific case file
@app.get("/case_files/{cnr}")
def read_case_file_state(cnr: int, session: SessionDependancy):
    case_file = session.get(CaseFile, cnr)
    if not case_file:
        raise HTTPException(status_code=404, detail=f"Case file with CNR '{cnr}' not found.")
    return {"case_file": {"cnr": case_file.cnr, "state": case_file.file_state.label}}


# Update the state of a case file
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

    case_file.file_state_id = file_state_id
    session.add(case_file)
    session.commit()
    session.refresh(case_file)

    return {"message": "Case file state updated successfully", "case_file": {"cnr": case_file.cnr, "state": case_file.file_state.label}}


# Delete a case file
@app.delete("/case_files/{cnr}")
def delete_case_file(cnr: int, session: SessionDependancy):
    case_file = session.get(CaseFile, cnr)
    if not case_file:
        raise HTTPException(status_code=404, detail=f"Case file with CNR '{cnr}' not found.")

    case_file_cnr = case_file.cnr
    case_file_state = case_file.file_state.label

    session.delete(case_file)
    session.commit()

    return {"message": "Case file deleted successfully", "case_file": {"cnr": case_file_cnr, "state": case_file_state}}
