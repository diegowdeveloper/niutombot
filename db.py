from typing import Annotated
from fastapi import FastAPI, Depends
from sqlmodel import Session, create_engine, SQLModel

sqlite_name = "db.sqlite3"
sqlite_url  = f"sqlite:///{sqlite_name}"
# sqlite_url  = f"postgresql://postgres:AXPcjlOnfXZwsqXUsJbJKrpxCCKNxxNZ@postgres.railway.internal:5432/railway"

engine = create_engine(sqlite_url)

def create_all_tables(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]