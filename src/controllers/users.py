from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.models.users import User
from src.schemas.users import UserCreate, UserRead, UserUpdate
from src.services.users import UserServiceDep
from src.utils.security import get_current_active_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, service: UserServiceDep):
    """Create a new user in the system."""
    return await service.create(user_data)


@router.get("/me/", response_model=UserRead)
async def read_user_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Retrieve the profile of the authenticated user."""
    return current_user


@router.patch("/me/", response_model=UserRead)
async def update_user_me(
    user_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: UserServiceDep,
):
    """Update the profile of the authenticated user."""
    return await service.update_me(current_user, user_data)


@router.delete("/me/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: UserServiceDep,
):
    """Remove the authenticated user's account from the system."""
    await service.delete(current_user.id)
