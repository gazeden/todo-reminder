from typing import Generator

from app.db.session import get_session

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session.
    """
    yield from get_session()
