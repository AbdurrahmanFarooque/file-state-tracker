from pydantic import BaseModel
from sqlmodel import SQLModel, Relationship, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User, SQLModel, table=True):
    user_id: int | None = Field(default=None, primary_key=True)
    hashed_password: str
    

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
