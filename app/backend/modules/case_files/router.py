from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select

from app.backend.database import SessionDependancy
from app.backend.models import (
    CaseFile,
    CaseFilePublic,
    CaseFileSend,
    CaseFileTransaction,
    TransactionStatus,
    FileLocation,
    User
)
from app.backend.core.security import oauth2_scheme
from app.backend.dependencies import get_current_active_user


router = APIRouter(
    prefix="/api/case_files",
    tags=["case files"]
)


# @app.post("/api/locations", tags=["files"])
# def create_location(location: FileLocationCreate, session: SessionDependancy):
#     # Check if the location already exists
#     location_exists = session.exec(select(FileLocation).where(FileLocation.name == location.name)).first() is not None
#     if location_exists:
#         raise HTTPException(status_code=400, detail=f"Location '{location.name}' already exists.")

#     # Create new FileLocation
#     db_location = FileLocation(name=location.name)
#     session.add(db_location)
#     session.commit()
#     session.refresh(db_location)

#     return {"message": "Location added successfully", "location": db_location.name}


# Upload a new case file (remove function?)
@router.post("/{cnr}")
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


# Read all case files that are assigned to user
@router.get("/", response_model=list[CaseFilePublic])
def list_case_files(
    session: SessionDependancy, 
    token: Annotated[str, Depends(oauth2_scheme)], 
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    case_files = session.exec(select(CaseFile).where(CaseFile.location_id == current_user.at_location)).all()

    case_files_public = [
        {
            "cnr": case_file.cnr,
            "location": case_file.file_location.name
        } for case_file in case_files
    ]

    print(case_files_public)
    return case_files_public


# Read a specific case file
@router.get("/{cnr}")
def read_case_file_location(cnr: int, session: SessionDependancy):
    case_file = session.get(CaseFile, cnr)
    if not case_file:
        raise HTTPException(status_code=404, detail=f"Case file with CNR '{cnr}' not found.")
    return {"case_file": {"cnr": case_file.cnr, "location": case_file.file_location.name}}


# Check 'Body - Nested Models'
@router.patch("/send")
def initiate_case_file_transaction(bundle: CaseFileSend, session: SessionDependancy):
    """
    - Assume CNR values are valid, selected from a list (not input manually)
    - Assume location is valid (selected from a dropdown)
    """
    for file_input in bundle.case_file_list:
        case_file = session.get(CaseFile, file_input.cnr)
        if case_file:
            print(case_file.cnr, case_file.file_location.name, bundle.send_to_location.name)
            send_to_location_id = session.exec(
                select(FileLocation.location_id)
                .where(FileLocation.name == bundle.send_to_location.name)
            ).one()

            db_transaction = CaseFileTransaction(
                transaction_time=datetime.now(),
                cnr=case_file.cnr,
                sender_id=2,
                recipient_id=3,
                sent_from_location=case_file.file_location.location_id,
                sent_to_location=send_to_location_id,
                status=TransactionStatus.pending,
            )

            session.add(db_transaction)
            session.commit()
            session.refresh(db_transaction)
            
    return {"message": "transaction initiated"}


# Update the location of a case file
@router.patch("/{cnr}")
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
@router.delete("/{cnr}")
def delete_case_file(cnr: int, session: SessionDependancy):
    case_file = session.get(CaseFile, cnr)
    if not case_file:
        raise HTTPException(status_code=404, detail=f"Case file with CNR '{cnr}' not found.")

    case_file_cnr = case_file.cnr
    case_file_location = case_file.file_location.name

    session.delete(case_file)
    session.commit()

    return {"message": "Case file deleted successfully", "case_file": {"cnr": case_file_cnr, "location": case_file_location}}
