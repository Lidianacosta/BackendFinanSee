import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.fixture(name="categories_url")
def get_categories_url():
    return "/api/categories/"


@pytest_asyncio.fixture(name="categories")
async def populate_categories_table(
    client: AsyncClient, access_token: str, categories_url: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    categories = [
        (
            await client.post(
                categories_url,
                json={
                    "name": "Casa",
                    "description": "Gastos com a casa",
                },
                headers=headers,
            )
        ).json(),
        (
            await client.post(
                categories_url,
                json={
                    "name": "Alimentação",
                    "description": "Gastos com comida",
                },
                headers=headers,
            )
        ).json(),
    ]

    return categories
