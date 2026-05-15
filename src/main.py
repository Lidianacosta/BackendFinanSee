from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.controllers import auth, categories, expenses, periods, users
from src.utils.database import async_create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the FastAPI application."""
    await async_create_db_and_tables()
    yield


app = FastAPI(
    title="FinanSee API",
    description="Backend para controle financeiro pessoal",
    version="0.1.0",
    lifespan=lifespan,
)

API_PREFIX = "/api"

# Registrando os roteadores dos controllers
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(categories.router, prefix=API_PREFIX)
app.include_router(periods.router, prefix=API_PREFIX)
app.include_router(expenses.router, prefix=API_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint to verify the API is running."""
    return {"message": "Bem-vindo ao FinanSee API!"}
