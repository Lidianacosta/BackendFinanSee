"""User service layer.

Provides business logic and database interactions for managing users.
"""

import uuid
from datetime import date
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlmodel import col, select

from src.models.users import User
from src.schemas.users import UserCreate, UserUpdate
from src.services.periods import PeriodServiceDep
from src.utils.database import AsyncSessionDep
from src.utils.password import get_password_hash


class UserService:
    """Service class for User management."""

    def __init__(
        self, session: AsyncSessionDep, period_service: PeriodServiceDep
    ) -> None:
        """Initialize the user service with required dependencies."""
        self.session = session
        self.period_service = period_service

    async def create(self, user_create: UserCreate) -> User:
        """Create a new user and ensure they don't already exist."""
        existing_user = await self.get_user_by_email(user_create.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="E-mail já cadastrado")

        user_data = user_create.model_dump(
            exclude={"confirm_password", "password"}
        )
        user = User(
            **user_data,
            hashed_password=get_password_hash(user_create.password),
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def read(self, user_id: uuid.UUID) -> User:
        """Retrieve a user by their ID."""
        return await self.__get_by_id(user_id)

    async def update(
        self, user_id: uuid.UUID, user_update: UserUpdate
    ) -> User:
        """Update an existing user by ID."""
        user = await self.__get_by_id(user_id)
        return await self.update_me(user, user_update)

    async def update_me(self, user: User, user_update: UserUpdate) -> User:
        """Update the currently authenticated user and sync income with current period."""
        data = user_update.model_dump(exclude_unset=True)

        income_changed = "income" in data and data["income"] != user.income

        if "password" in data:
            user.hashed_password = get_password_hash(data.pop("password"))

        for attr, value in data.items():
            setattr(user, attr, value)

        self.session.add(user)

        if income_changed:
            current_period = await self.period_service.get_or_create_by_date(
                user.id, date.today()
            )
            current_period.total_income = user.income
            self.session.add(current_period)

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user_id: uuid.UUID) -> None:
        """Delete a user."""
        user = await self.__get_by_id(user_id)
        await self.session.delete(user)
        await self.session.commit()

    async def get_user_by_email(self, email: str) -> User | None:
        """Retrieve a user by their email."""
        statement = select(User).where(col(User.email) == email)
        result = await self.session.exec(statement)
        return result.first()

    async def __get_by_id(self, user_id: uuid.UUID) -> User:
        """Internal helper to retrieve a user by ID."""
        user = await self.session.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=404, detail="Usuário não encontrado"
            )
        return user


UserServiceDep = Annotated[UserService, Depends(UserService)]
