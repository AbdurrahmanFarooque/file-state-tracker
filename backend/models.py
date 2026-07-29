from enum import Enum
from pydantic import BaseModel
from sqlmodel import SQLModel, Relationship, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserRole(str, Enum):
    section_assistant = "section assistant"
    listing_officer = "listing officer"


class UserBase(SQLModel):
    full_name: str | None = None
    email: str | None = None


class UserPublic(UserBase):
    username: str
    user_role: UserRole
    disabled: bool


class UserCreate(UserBase):
    username: str
    password: str
    disabled: bool | None = False
    user_role: UserRole = UserRole.section_assistant


class UserUpdate(UserBase):
    pass


class User(UserBase, SQLModel, table=True):
    user_id: int | None = Field(default=None, primary_key=True)
    username: str
    user_role: UserRole
    hashed_password: str
    disabled: bool
    

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
