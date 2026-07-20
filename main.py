from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from sqlmodel import select

from models import Hero, HeroCreate, HeroPublic, HeroUpdate, CaseFile
from database import create_db_and_tables, SessionDependancy


app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/heroes/", response_model=HeroPublic)
def create_hero(hero: HeroCreate, session: SessionDependancy):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero


@app.get("/heroes/", response_model=list[HeroPublic])
def read_heroes(session: SessionDependancy, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100):
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes


@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(hero_id: int, session: SessionDependancy):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero


@app.patch("/heroes/{hero_id}", response_model=HeroPublic)
def update_hero(hero_id: int, hero: HeroUpdate, session: SessionDependancy):
    hero_db = session.get(Hero, hero_id)
    if not hero_db:
        raise HTTPException(status_code=404, detail="Hero not found")
    hero_data = hero.model_dump(exclude_unset=True)
    hero_db.sqlmodel_update(hero_data)
    session.add(hero_db)
    session.commit()
    session.refresh(hero_db)
    return hero_db


@app.delete("/heroes/{hero_id}")
def delete_hero(hero_id: int, session: SessionDependancy):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}

# ============================================================================

case_files: dict[int, CaseFile] = {}
FILE_STATES = {
    "section": {"listing", "records"},
    "listing": {"court"},
    "court": {"chamber", "section"}, 
    "chamber": {"section"}, 
    "records": {"section"}
}


# Assume section assistant uploads the file
@app.post("/case_files/")
def upload_case_file(case_file: CaseFile, session: SessionDependancy):
    db_case_file = CaseFile.model_validate(case_file)
    session.add((db_case_file))
    session.commit()
    session.refresh(db_case_file)
    return db_case_file    


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.put("/case_files/update/{cnr}")
def update_case_file_state(cnr: int, state: str):
    pass


@app.get("/case_files/{cnr}")
def read_case_file_state(cnr: int):
    pass


@app.get("/case_files")
def list_case_files():
    pass

