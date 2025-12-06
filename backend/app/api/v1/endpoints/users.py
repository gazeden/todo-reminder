import logging
from typing import Any

from app.api.deps import (
    CommonQueryParams,
    get_current_active_user,
    get_current_superuser,
    get_db,
)
from app.crud.user import user_crud
from app.models.user import User
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from fastapi import APIRouter, Depends, HTTPException, status
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


@router.get("/me", response_model=UserResponse)
async def read_user_me(current_user: User = Depends(get_current_active_user)) -> Any:
    """
    Get current user.
    """
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific user by ID.
    Users can only read their own data unless they're superusers.
    """
    user = user_crud.get(db, id=user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check permissions
    if user.id != current_user.id and not user_crud.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Create new user.
    """
    # Check if user already exists
    user = user_crud.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )
    
    user = user_crud.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists"
        )
    
    # Create user
    user = user_crud.create(db, obj_in=user_in)
        
    return user
