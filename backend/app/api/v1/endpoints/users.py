import logging
from typing import Any

from app.api.deps import CommonQueryParams, get_current_superuser, get_db
from app.crud.user import user_crud
from app.models.user import User
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from fastapi import APIRouter, Depends
from sqlmodel import Session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=UserListResponse)
async def list_users(
    db: Session = Depends(get_db),
    commons: CommonQueryParams = Depends(),
    current_user: User = Depends(get_current_superuser),
) -> Any:
    """
    Retrieve users. Only accessible by superusers.
    """
    users = user_crud.get_multi(db, skip=commons.skip, limit=commons.limit)
    total = user_crud.count(db)

    return UserListResponse(
        users=users,
        total=total,
        page=commons.skip // commons.limit + 1,
        page_size=commons.limit,
    )
