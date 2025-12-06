from app.crud.base import CRUDBase
from app.models import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """
    CRUD operations for User model.
    """


user_crud = CRUDUser(User)
