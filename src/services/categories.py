"""Category service layer.

Handles business logic for category management, including CRUD operations
and duplicate checks.
"""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from src.models.categories import Category
from src.schemas.categories import CategoryCreate, CategoryUpdate
from src.utils.database import AsyncSessionDep


class CategoryService:
    """Service for category-related operations."""

    def __init__(self, session: AsyncSessionDep) -> None:
        """Initialize CategoryService with a database session."""
        self.session = session

    async def create(
        self, category_create: CategoryCreate, user_id: uuid.UUID
    ) -> Category:
        """Create a new category for the authenticated user."""
        statement = select(Category).where(
            col(Category.user_id) == user_id,
            col(Category.name) == category_create.name,
        )
        result = await self.session.exec(statement)
        if result.first():
            raise HTTPException(
                status_code=400,
                detail="Já existe uma categoria com este nome",
            )

        category = Category(**category_create.model_dump(), user_id=user_id)
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)

        return await self.read(category.id, user_id)

    async def read_all(self, user_id: uuid.UUID) -> list[Category]:
        """List all categories for the authenticated user."""
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
        """Retrieve a specific category ensuring it belongs to the user."""
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
            raise HTTPException(
                status_code=404,
                detail="Categoria não encontrada",
            )
        return category

    async def update(
        self,
        category_id: uuid.UUID,
        category_update: CategoryUpdate,
        user_id: uuid.UUID,
    ) -> Category:
        """Update a category and check for name duplicates."""
        category = await self.read(category_id, user_id)
        data = category_update.model_dump(exclude_unset=True)

        if "name" in data and data["name"] != category.name:
            statement = select(Category).where(
                col(Category.user_id) == user_id,
                col(Category.name) == data["name"],
                col(Category.id) != category_id,
            )
            result = await self.session.exec(statement)
            if result.first():
                raise HTTPException(
                    status_code=400,
                    detail="Já existe uma categoria com este nome",
                )

        for attr, value in data.items():
            setattr(category, attr, value)

        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return await self.read(category.id, user_id)

    async def delete(self, category_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a category for the authenticated user."""
        category = await self.read(category_id, user_id)
        
        if category.expenses:
            raise HTTPException(
                status_code=400,
                detail="Não é possível deletar uma categoria que possui despesas"
            )
            
        await self.session.delete(category)
        await self.session.commit()


CategoryServiceDep = Annotated[CategoryService, Depends(CategoryService)]
