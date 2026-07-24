"""Unit tests for UserService business rules."""

from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException

from src.models.users import User
from src.schemas.users import UserCreate, UserUpdate
from src.services.users import UserService
from src.utils.password import get_password_hash


async def _make_user(db, email="user@test.com", income=Decimal("1000")):
    """Helper: insert a user directly and return it."""
    user = User(
        name="Test",
        email=email,
        hashed_password=get_password_hash("password123"),
        income=income,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_user_duplicate_email_fails(db):
    """create() should reject an email that already exists."""
    ps = await _make_user(db, email="dup@test.com")
    from src.services.periods import PeriodService

    us = UserService(db, PeriodService(db))

    with pytest.raises(HTTPException) as exc:
        await us.create(
            UserCreate(
                name="Other",
                email=ps.email or "",
                password="password123",
                confirm_password="password123",
            )
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_update_me_without_income_change_keeps_periods_untouched(db):
    """update_me with no income change should not touch current period."""
    from src.services.periods import PeriodService

    user = await _make_user(db, income=Decimal("1000"))
    ps = PeriodService(db)
    us = UserService(db, ps)

    updated = await us.update_me(user, UserUpdate(name="Novo Nome"))
    assert updated.name == "Novo Nome"
    # Should not have created a period for current month automatically
    periods = await ps.read_all(user.id)
    assert periods == []


@pytest.mark.asyncio
async def test_update_me_with_income_change_syncs_current_period(db):
    """update_me with new income should also update current period income."""

    from src.services.periods import PeriodService

    user = await _make_user(db, income=Decimal("1000"))
    ps = PeriodService(db)
    us = UserService(db, ps)

    new_income = Decimal("2500")
    await us.update_me(user, UserUpdate(income=new_income))

    current = await ps.get_or_create_by_date(user.id, date.today())
    assert current.total_income == new_income


@pytest.mark.asyncio
async def test_update_me_with_password_change(db):
    """update_me with password should update the hashed_password."""
    from src.services.periods import PeriodService

    user = await _make_user(db)
    ps = PeriodService(db)
    us = UserService(db, ps)

    old_hash = user.hashed_password
    await us.update_me(user, UserUpdate(password="new-pwd-123"))
    await db.refresh(user)
    assert user.hashed_password != old_hash


@pytest.mark.asyncio
async def test_delete_me_removes_user(db):
    """delete_me should remove the user from the DB."""
    from src.services.periods import PeriodService

    user = await _make_user(db, email="todelete@test.com")
    ps = PeriodService(db)
    us = UserService(db, ps)

    await us.delete_me(user)

    from sqlmodel import col, select

    stmt = select(User).where(col(User.email) == "todelete@test.com")
    assert (await db.exec(stmt)).first() is None


@pytest.mark.asyncio
async def test_reset_password_user_not_found(db):
    """reset_password should 404 for unknown email."""
    from src.services.periods import PeriodService

    ps = PeriodService(db)
    us = UserService(db, ps)

    with pytest.raises(HTTPException) as exc:
        await us.reset_password("unknown@test.com", "new-pwd-123")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_reset_password_success(db):
    """reset_password should update the hashed_password for known user."""
    from src.services.periods import PeriodService

    user = await _make_user(db, email="reset@test.com")
    ps = PeriodService(db)
    us = UserService(db, ps)

    old_hash = user.hashed_password
    await us.reset_password(user.email or "", "new-pwd-123")
    await db.refresh(user)
    assert user.hashed_password != old_hash


@pytest.mark.asyncio
async def test_get_user_by_email_returns_none_for_unknown(db):
    """get_user_by_email should return None for unknown email."""
    from src.services.periods import PeriodService

    ps = PeriodService(db)
    us = UserService(db, ps)

    assert await us.get_user_by_email("does-not-exist@test.com") is None
