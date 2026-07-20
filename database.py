from typing import Annotated

from fastapi import Depends
from sqlmodel import create_engine, SQLModel, Session


postgres_url = "postgresql://postgres:1234@localhost:5432/postgres"

engine = create_engine(postgres_url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session

SessionDependancy = Annotated[Session, Depends(get_session)]