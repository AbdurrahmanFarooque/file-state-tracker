from sqlmodel import SQLModel, Field


class CaseFile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    cnr: int = Field(index=True)
    state: str = Field(default=None, index=True)


