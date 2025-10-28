import os
from dotenv import load_dotenv
from typing import Annotated
from fastapi import FastAPI, Depends
from sqlmodel import Session, create_engine, SQLModel

load_dotenv()

engine = create_engine(os.getenv("SQLALCHEMY_DATABASE_URL"))

def create_all_tables(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]