from typing import Annotated

from fastapi import Depends
from sqlmodel import select, create_engine, SQLModel, Session

from models import FileState


postgres_url = "postgresql://postgres:1234@localhost:5432/postgres"

connect_args = {"check_same_thread": False}
engine = create_engine(postgres_url, echo=True, connect_args=connect_args) # Remove echo=True in production


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def populate_filestate():
    with Session(engine) as session:
        filestate_is_empty = session.exec(select(FileState)).first() is None

        if filestate_is_empty:
            filestate_filing = FileState(label="filing")
            filestate_section = FileState(label="section")
            filestate_listing = FileState(label="listing")
            filestate_court = FileState(label="court")
            filestate_chamber = FileState(label="chamber")
            filestate_records = FileState(label="records")

            session.add(filestate_filing)
            session.add(filestate_section)
            session.add(filestate_listing)
            session.add(filestate_court)
            session.add(filestate_chamber)
            session.add(filestate_records)
            session.commit()


SessionDependancy = Annotated[Session, Depends(get_session)]