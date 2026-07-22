from typing import Optional

from pydantic import BaseModel
from sqlmodel import SQLModel, Field


# case_file
class CaseFile(SQLModel, table=True):
    cnr: int = Field(primary_key=True)
    state_id: int | None = Field(default=None, foreign_key="filestate.id")


# file_state
class FileState(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    label: str = Field(unique=True)