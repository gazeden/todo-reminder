import os
from contextlib import contextmanager

from app.config import settings
from sqlmodel import Session, SQLModel, create_engine

engine = create_engine(settings.DATABASE_URL, echo=True)


@contextmanager
def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    SQLModel.metadata.create_all(engine)
