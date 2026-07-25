"""Main entry point for the FinanSee API.

This module initializes the FastAPI application, sets up the database,
configures CORS and logging, and includes all the application routers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.controllers import auth, categories, expenses, periods, users
from src.core.config import settings
from src.core.logging import RequestLoggingMiddleware, configure_logging
from src.utils.database import async_create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the FastAPI application.

    Production runs Alembic migrations via CI. In development and test
    environments we fall back to SQLModel.metadata.create_all for ease
    of use and in-memory SQLite in tests.
    """
    configure_logging()
    if settings.environment != "production":
        await async_create_db_and_tables()
    yield


app = FastAPI(
    title="FinanSee API",
    description="Backend para controle financeiro pessoal",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(categories.router, prefix=API_PREFIX)
app.include_router(periods.router, prefix=API_PREFIX)
app.include_router(expenses.router, prefix=API_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint to verify the API is running."""
    return {"message": "Bem-vindo ao FinanSee API!"}
