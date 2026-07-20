from pydantic import BaseModel
from sqlmodel import SQLModel, Field


class CaseFile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    cnr: int = Field(index=True)
    state: str = Field(default=None, index=True)


class HeroBase(SQLModel):
    name: str = Field(index=True)
    age: int = Field(default=None, index=True)


class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    secret_name: str


class HeroPublic(HeroBase):
    id: int


class HeroCreate(HeroBase):
    secret_name: str


class HeroUpdate(HeroBase):
    name: str | None = None
    age: str | None = None
    secret_name: str | None = None


