import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.models.pending_action import PendingAction, PendingActionStatus


async def get_active_for_user(
    session: AsyncSession, user_id: str
) -> list[PendingAction]:
    """Return all non-expired PENDING actions for a user, newest first."""
    now = datetime.now(UTC)
    result = await session.execute(
        select(PendingAction)
        .where(
            PendingAction.user_id == user_id,
            PendingAction.status == PendingActionStatus.PENDING,
            (PendingAction.expired_at.is_(None)) | (PendingAction.expired_at > now),
        )
        .order_by(PendingAction.created_at.desc())
    )
    return list(result.scalars().all())


async def get_by_id(
    session: AsyncSession, action_id: uuid.UUID
) -> PendingAction | None:
    return await session.get(PendingAction, action_id)


async def create(
    session: AsyncSession,
    *,
    user_id: str,
    action_name: str,
    expired_at: datetime | None = None,
    meta: dict | None = None,
) -> PendingAction:
    action = PendingAction(
        user_id=user_id,
        action_name=action_name,
        status=PendingActionStatus.PENDING,
        expired_at=expired_at,
        meta=meta,
    )
    session.add(action)
    await session.flush()  # populate id without committing
    return action


async def update_status(
    session: AsyncSession,
    action_id: uuid.UUID,
    status: PendingActionStatus,
) -> PendingAction | None:
    action = await session.get(PendingAction, action_id)
    if action is None:
        return None
    action.status = status
    action.updated_at = datetime.now(UTC)
    await session.flush()
    return action
