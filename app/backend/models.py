from enum import Enum
from pydantic import BaseModel
from sqlmodel import SQLModel, Relationship, Field

from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class TransactionStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    canceled = "canceled"


class UserRole(str, Enum):
    section_assistant = "section assistant"
    listing_officer = "listing officer"
    court_officer = "court officer"
    personal_secretary = "personal secretary"


class UserBase(BaseModel):
    username: str
    full_name: str | None = None
    email: str | None = None
    role: UserRole = UserRole.section_assistant


class UserPublic(UserBase):
    pass


class UserCreate(UserBase):
    password: str
    disabled: bool | None = False

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "john123",
                    "full_name": "John Doe",
                    "email": "john@example.com",
                    "role": "section assistant",
                    "password": "1122",
                }
            ]
        }
    }


class User(UserBase, SQLModel, table=True):
    user_id: int | None = Field(default=None, primary_key=True)
    disabled: bool
    hashed_password: str

    at_location: int | None = Field(default=None, foreign_key="filelocation.location_id")


class UserUpdate(BaseModel):
    full_name: str | None = User.full_name
    email: str | None = User.email

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "full_name": "John Doe",
                    "email": "john@example.com"
                }
            ]
        }
    }

    
class CaseFileTransaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    transaction_time: datetime | None = None
    cnr: int = Field(foreign_key="casefile.cnr")
    sender_id: int = Field(foreign_key="user.user_id")
    recipient_id: int = Field(foreign_key="user.user_id")
    sent_from_location: int | None = Field(foreign_key="filelocation.location_id")
    sent_to_location: int | None = Field(foreign_key="filelocation.location_id")
    status: TransactionStatus | None = None

    case_file: "CaseFile" = Relationship(back_populates="transactions")


class CaseFileBase(BaseModel):
    cnr: int


class CaseFile(CaseFileBase, SQLModel, table=True):
    cnr: int = Field(primary_key=True)
    location_id: int | None = Field(default=None, foreign_key="filelocation.location_id")

    file_location: "FileLocation" = Relationship(back_populates="case_files")
    transactions: list["CaseFileTransaction"] = Relationship(back_populates="case_file")


class CaseFilePublic(CaseFileBase):
    location: str


class FileLocationBase(BaseModel):
    name: str


class FileLocation(FileLocationBase, SQLModel, table=True):
    location_id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    case_files: list["CaseFile"] = Relationship(back_populates="file_location")


class FileLocationCreate(FileLocationBase):
    pass


class CaseFileSend(BaseModel):
    case_file_list: list[CaseFileBase]
    send_to_location: FileLocationBase