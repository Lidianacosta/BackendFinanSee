"""Base database model for FinanSee.

This module provides common fields and configuration for all SQLModel entities.
"""

import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class BaseModel(SQLModel, table=False):
    """Common base class for all database models.

    Provides a UUID primary key and a creation timestamp.
    """

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, unique=True, primary_key=True
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
