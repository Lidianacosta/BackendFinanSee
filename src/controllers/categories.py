import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.models.users import User
from src.schemas.categories import CategoryCreate, CategoryRead, CategoryUpdate
from src.services.categories import CategoryServiceDep
from src.utils.security import get_current_active_user

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post(
    "/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED
)
async def create_category(
    category_data: CategoryCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: CategoryServiceDep,
):
    """Cria uma nova categoria para o usuário autenticado."""
    return await service.create(category_data, current_user.id)


@router.get("/", response_model=list[CategoryRead])
async def read_categories(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: CategoryServiceDep,
):
    """Lista todas as categorias do usuário autenticado."""
    return await service.read_all(current_user.id)


@router.get("/{category_id}", response_model=CategoryRead)
async def read_category(
    category_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: CategoryServiceDep,
):
    """Busca os detalhes de uma categoria específica."""
    return await service.read(category_id, current_user.id)


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: uuid.UUID,
    category_data: CategoryUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: CategoryServiceDep,
):
    """Atualiza uma categoria existente."""
    return await service.update(category_id, category_data, current_user.id)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: CategoryServiceDep,
):
    """Remove uma categoria do sistema."""
    await service.delete(category_id, current_user.id)
