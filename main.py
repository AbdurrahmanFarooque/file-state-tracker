from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from sqlmodel import select

from models import CaseFile
from database import create_db_and_tables, SessionDependancy


app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


case_files: dict[int, CaseFile] = {}
FILE_STATES = {
    "section": {"listing", "records"},
    "listing": {"court"},
    "court": {"chamber", "section"}, 
    "chamber": {"section"}, 
    "records": {"section"}
}


# Assume section assistant uploads the file
@app.post("/case_files/")
def upload_case_file(case_file: CaseFile, session: SessionDependancy):
    db_case_file = CaseFile.model_validate(case_file)
    session.add((db_case_file))
    session.commit()
    session.refresh(db_case_file)
    return db_case_file    


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.put("/case_files/update/{cnr}")
def update_case_file_state(cnr: int, state: str):
    pass


@app.get("/case_files/{cnr}")
def read_case_file_state(cnr: int):
    pass


@app.get("/case_files")
def list_case_files():
    pass

