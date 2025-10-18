from dotenv import load_dotenv, find_dotenv
import os
from models import Summary, Dependency, UserKnowledge, CodeMapping  # noqa: F401
from sqlmodel import SQLModel, create_engine

load_dotenv(find_dotenv())

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
