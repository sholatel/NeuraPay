"""
Pending action tools — callable by agents that need human-in-the-loop state.

These tools write to the ai-service's own PostgreSQL table (pending_actions).
They do NOT call the NestJS banking backend.

Design:
  - create_pending_action  → agent stores mid-flow state before handing back to the user
  - update_pending_action  → agent marks the flow complete (resolved) or aborted (canceled)

The DB session is held on RequestContext.db_session; the final commit happens
in operations.py after Runner.run() returns successfully.
"""

import uuid
from datetime import UTC, datetime, timedelta

from agents import RunContextWrapper, function_tool

from app.agents.base import RequestContext
from app.core.logging import get_logger
from app.db.constants import PendingActionName
from app.db.models.pending_action import PendingActionStatus
from app.repositories import pending_action as repo

logger = get_logger(__name__)

_VALID_STATUSES = {s.value for s in PendingActionStatus} - {"pending"}


@function_tool(strict_mode=False)
async def create_pending_action(
    ctx: RunContextWrapper[RequestContext],
    action_name: str,
    expires_in_minutes: int = 5,
    meta: dict | None = None,
) -> str:
    """
    Create a pending action to preserve mid-flow state across voice requests.

    Use this when you need the user to respond before the flow can continue
    (e.g., awaiting transfer confirmation). The pending action is detected on
    the user's next request and injected into your context automatically.

    Args:
        action_name:         One of the defined action name constants:
                               TRANSFER_CONFIRM_RECIPIENT
                               TRANSFER_CONFIRM_AMOUNT
                               TRANSFER_AWAIT_CONFIRMATION
        expires_in_minutes:  How long to keep the action pending (default 5).
                             After this time the action is considered expired
                             and will not be surfaced to you.
        meta:                Free-form key-value pairs that capture the state
                             needed to continue the flow (e.g. recipient account
                             number, amount). Keep values as strings.

    Returns:
        Confirmation string with the new action ID, or an error message.
    """
    if ctx.context.db_session is None:
        return "Error: database session is not available for this request."

    if action_name not in PendingActionName.ALL:
        valid = ", ".join(sorted(PendingActionName.ALL))
        return f"Invalid action_name '{action_name}'. Must be one of: {valid}"

    expired_at = datetime.now(UTC) + timedelta(minutes=expires_in_minutes)

    try:
        action = await repo.create(
            ctx.context.db_session,
            user_id=ctx.context.user_id,
            action_name=action_name,
            expired_at=expired_at,
            meta=meta,
        )
        logger.info(
            "pending_action.created",
            action_id=str(action.id),
            action_name=action_name,
            user_id=ctx.context.user_id,
            expires_at=expired_at.isoformat(),
        )
        return (
            f"Pending action created.\n"
            f"ID:      {action.id}\n"
            f"Action:  {action_name}\n"
            f"Expires: {expired_at.strftime('%H:%M UTC')}"
        )
    except Exception as exc:
        logger.error("pending_action.create_failed", error=str(exc), user_id=ctx.context.user_id)
        return f"Failed to create pending action: {exc}"


@function_tool
async def update_pending_action(
    ctx: RunContextWrapper[RequestContext],
    action_id: str,
    status: str,
) -> str:
    """
    Update the status of a pending action to mark it resolved or canceled.

    Call this after the user confirms or cancels a multi-step flow so the
    action is not presented again on the next request.

    Args:
        action_id:  The UUID returned by create_pending_action.
        status:     Either "resolved" (flow completed) or "canceled" (flow aborted).

    Returns:
        Confirmation string, or an error message.
    """
    if ctx.context.db_session is None:
        return "Error: database session is not available for this request."

    if status not in _VALID_STATUSES:
        return f"Invalid status '{status}'. Must be one of: {', '.join(sorted(_VALID_STATUSES))}"

    try:
        action_uuid = uuid.UUID(action_id)
    except ValueError:
        return f"Invalid action_id '{action_id}' — must be a valid UUID."

    try:
        updated = await repo.update_status(
            ctx.context.db_session,
            action_uuid,
            PendingActionStatus(status),
        )
        if updated is None:
            return f"No pending action found with ID {action_id}."

        logger.info(
            "pending_action.updated",
            action_id=action_id,
            new_status=status,
            user_id=ctx.context.user_id,
        )
        return f"Pending action {action_id} marked as {status}."
    except Exception as exc:
        logger.error("pending_action.update_failed", error=str(exc), action_id=action_id)
        return f"Failed to update pending action: {exc}"
