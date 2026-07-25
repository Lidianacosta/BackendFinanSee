"""Unit tests for CategoryService business rules."""

import uuid

import pytest
from fastapi import HTTPException

from src.schemas.categories import CategoryCreate, CategoryUpdate
from src.services.categories import CategoryService


@pytest.mark.asyncio
async def test_read_category_not_found(db):
    """read() raises 404 when category does not exist."""
    cs = CategoryService(db)
    category_id = uuid.uuid4()
    user_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc:
        await cs.read(category_id, user_id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_category_name_to_existing_fails(db):
    """update() raises 400 when renaming to an existing name (same user)."""
    uid = uuid.uuid4()
    cs = CategoryService(db)
    await cs.create(CategoryCreate(name="Alimentação"), uid)
    cat2 = await cs.create(CategoryCreate(name="Lazer"), uid)
    update_data = CategoryUpdate(name="Alimentação")

    with pytest.raises(HTTPException) as exc:
        await cs.update(cat2.id, update_data, uid)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_update_category_same_name_succeeds(db):
    """Updating a category to its own name should not be a duplicate."""
    uid = uuid.uuid4()
    cs = CategoryService(db)
    cat = await cs.create(CategoryCreate(name="Casa"), uid)

    updated = await cs.update(
        cat.id, CategoryUpdate(description="Nova descrição"), uid
    )
    assert updated.description == "Nova descrição"
    assert updated.name == "Casa"


@pytest.mark.asyncio
async def test_update_category_new_name_succeeds(db):
    """Renaming to a brand new name should work."""
    uid = uuid.uuid4()
    cs = CategoryService(db)
    cat = await cs.create(CategoryCreate(name="Antigo"), uid)

    updated = await cs.update(cat.id, CategoryUpdate(name="Novo"), uid)
    assert updated.name == "Novo"


@pytest.mark.asyncio
async def test_delete_category_without_expenses_succeeds(db):
    """Deleting a category when it has no expenses should succeed."""
    uid = uuid.uuid4()
    cs = CategoryService(db)
    cat = await cs.create(CategoryCreate(name="Vazia"), uid)

    await cs.delete(cat.id, uid)

    with pytest.raises(HTTPException) as exc:
        await cs.read(cat.id, uid)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_read_all_returns_only_user_categories(db):
    """read_all should only return categories belonging to the user."""
    uid_a = uuid.uuid4()
    uid_b = uuid.uuid4()
    cs = CategoryService(db)
    await cs.create(CategoryCreate(name="UserA"), uid_a)
    await cs.create(CategoryCreate(name="UserB"), uid_b)

    cats_a = await cs.read_all(uid_a)
    cats_b = await cs.read_all(uid_b)

    assert {c.name for c in cats_a} == {"UserA"}
    assert {c.name for c in cats_b} == {"UserB"}
