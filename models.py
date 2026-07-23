from typing import Optional

from pydantic import BaseModel
from sqlmodel import SQLModel, Relationship, Field


# case_file
class CaseFile(SQLModel, table=True):
    cnr: int = Field(primary_key=True)
    file_state_id: int | None = Field(default=None, foreign_key="filestate.id")

    file_state: "FileState" = Relationship(back_populates="case_files")


# file_state
class FileState(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    label: str = Field(unique=True)

    case_files: list["CaseFile"] = Relationship(back_populates="file_state")
