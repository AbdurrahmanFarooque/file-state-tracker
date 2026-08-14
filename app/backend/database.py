from typing import Annotated

from fastapi import Depends
from sqlmodel import select, create_engine, SQLModel, Session

from app.backend.models import FileLocation


POSTGRES_URL = "postgresql://postgres:1234@localhost:5432/postgres"

connect_args = {"check_same_thread": False}
engine = create_engine(POSTGRES_URL, echo=False) # Remove echo=True in production # connect_args=connect_args


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def populate_filelocation():
    with Session(engine) as session:
        filelocation_is_empty = session.exec(select(FileLocation)).first() is None

        if filelocation_is_empty:
            filelocation_filing = FileLocation(name="filing")
            filelocation_section = FileLocation(name="section")
            filelocation_listing = FileLocation(name="listing")
            filelocation_court = FileLocation(name="court")
            filelocation_chamber = FileLocation(name="chamber")
            filelocation_records = FileLocation(name="records")

            session.add(filelocation_filing)
            session.add(filelocation_section)
            session.add(filelocation_listing)
            session.add(filelocation_court)
            session.add(filelocation_chamber)
            session.add(filelocation_records)
            session.commit()


SessionDependancy = Annotated[Session, Depends(get_session)]