import enum
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel


class PendingActionStatus(str, enum.Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    CANCELED = "canceled"


class PendingAction(SQLModel, table=True):
    __tablename__ = "pending_actions"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    )
    action_name: str
    status: PendingActionStatus = Field(
        default=PendingActionStatus.PENDING,
        sa_column=Column(
            SAEnum(PendingActionStatus, name="pending_action_status"),
            nullable=False,
            default=PendingActionStatus.PENDING,
        ),
    )
    user_id: str = Field(index=True)
    expired_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    meta: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
