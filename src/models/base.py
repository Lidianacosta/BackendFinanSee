import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class BaseModel(SQLModel, table=False):
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4, unique=True, primary_key=True
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
