"""Category service layer."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from src.models.categories import Category
from src.schemas.categories import CategoryCreate, CategoryUpdate
from src.utils.database import AsyncSessionDep


class CategoryService:
    def __init__(self, session: AsyncSessionDep) -> None:
        self.session = session

    async def create(
        self, category_create: CategoryCreate, user_id: uuid.UUID
    ) -> Category:
        """Cria uma nova categoria para o usuário logado."""
        # Verifica se já existe uma categoria com este nome para o usuário
        statement = select(Category).where(
            col(Category.user_id) == user_id,
            col(Category.name) == category_create.name,
        )
        result = await self.session.exec(statement)
        if result.first():
            raise HTTPException(
                status_code=400,
                detail="Category with this name already exists",
            )

        category = Category(**category_create.model_dump(), user_id=user_id)
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def read_all(self, user_id: uuid.UUID) -> list[Category]:
        """Lista todas as categorias do usuário logado."""
        statement = (
            select(Category)
            .where(col(Category.user_id) == user_id)
            .options(selectinload(Category.expenses))
        )
        result = await self.session.exec(statement)
        return list(result.all())

    async def read(
        self, category_id: uuid.UUID, user_id: uuid.UUID
    ) -> Category:
        """Busca uma categoria específica garantindo que pertence ao usuário."""
        statement = (
            select(Category)
            .where(
                col(Category.id) == category_id,
                col(Category.user_id) == user_id,
            )
            .options(selectinload(Category.expenses))
        )
        result = await self.session.exec(statement)
        category = result.first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return category

    async def update(
        self,
        category_id: uuid.UUID,
        category_update: CategoryUpdate,
        user_id: uuid.UUID,
    ) -> Category:
        """Atualiza uma categoria do usuário logado."""
        category = await self.read(category_id, user_id)
        data = category_update.model_dump(exclude_unset=True)

        for attr, value in data.items():
            setattr(category, attr, value)

        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def delete(self, category_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Deleta uma categoria do usuário logado."""
        category = await self.read(category_id, user_id)
        await self.session.delete(category)
        await self.session.commit()


CategoryServiceDep = Annotated[CategoryService, Depends(CategoryService)]
