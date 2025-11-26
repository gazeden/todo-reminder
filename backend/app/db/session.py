import os
from contextlib import contextmanager

from sqlmodel import Session, create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/todo_reminder"
)

engine = create_engine(DATABASE_URL, echo=True)


@contextmanager
def get_session():
    with Session(engine) as session:
        yield session
