from app.crud.base import CRUDBase
from app.models import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """
    CRUD operations for User model.
    """

    def is_active(self, user: User) -> bool:
        """Check if user is active."""
        return user.is_active


user_crud = CRUDUser(User)
