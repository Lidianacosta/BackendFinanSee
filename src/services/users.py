"""User service layer.

Provides business logic and database interactions for managing users.
"""

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

    async def update_me(self, user: User, user_update: UserUpdate) -> User:
        """Update the currently authenticated user and sync income with current period."""
        data = user_update.model_dump(exclude_unset=True)

        new_income = data.get("income")
        income_changed = new_income is not None and new_income != user.income

        if "password" in data:
            user.hashed_password = get_password_hash(data.pop("password"))

        for attr, value in data.items():
            setattr(user, attr, value)

        self.session.add(user)

        if income_changed:
            current_period = await self.period_service.get_or_create_by_date(
                user.id, date.today()
            )
            current_period.total_income = new_income  # type: ignore[assignment]
            self.session.add(current_period)

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete_me(self, user: User) -> None:
        """Delete a user."""
        await self.session.delete(user)
        await self.session.commit()

    async def get_user_by_email(self, email: str) -> User | None:
        """Retrieve a user by their email."""
        statement = select(User).where(col(User.email) == email)
        result = await self.session.exec(statement)
        return result.first()

    async def reset_password(self, email: str, new_password: str) -> None:
        """Reset a user's password."""
        user = await self.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=404, detail="Usuário não encontrado"
            )

        user.hashed_password = get_password_hash(new_password)
        self.session.add(user)
        await self.session.commit()


UserServiceDep = Annotated[UserService, Depends(UserService)]
