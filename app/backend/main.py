from fastapi import FastAPI

from app.backend.database import (
    create_db_and_tables, 
    populate_filelocation, 
    SessionDependancy
)
from app.backend.modules.users.router import router as users_router
from app.backend.modules.case_files.router import router as case_files_router
from app.backend.modules.tokens.router import router as token_router


app = FastAPI()

app.include_router(users_router)
app.include_router(case_files_router)
app.include_router(token_router)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    # populate_filelocation()
