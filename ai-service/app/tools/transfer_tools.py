"""
Transfer tools — callable by the Transfer_Agent.

Handles the execution of money transfers between platform users.
The agent prompt enforces a confirm-before-execute pattern; this tool
is only called after the user has explicitly confirmed the transfer.
"""

import uuid

from agents import RunContextWrapper, function_tool

from app.agents.base import RequestContext
from app.core.exceptions import BankingBackendError
from app.integrations.banking.client import kobo_to_ngn


def _generate_reference() -> str:
    """Generate a unique transaction reference for the banking backend.

    Format: AI-<16 uppercase hex chars>
    Satisfies the backend constraint: unique, 8–100 chars.
    """
    return f"AI-{uuid.uuid4().hex[:16].upper()}"


@function_tool
async def execute_transfer(
    ctx: RunContextWrapper[RequestContext],
    to_user_id: str,
    amount_ngn: float,
    currency: str = "NGN",
) -> str:
    """
    Execute a money transfer from the authenticated user to another platform user.

    IMPORTANT: Only call this after the user has explicitly confirmed the
    transfer summary. Show the recipient, amount, and currency first and
    ask for confirmation before invoking this tool.

    Args:
        to_user_id: The recipient's User ID (UUID).
        amount_ngn: Amount to transfer in Nigerian Naira (e.g. 5000 for ₦5,000).
        currency:   Currency code, defaults to NGN.

    Returns:
        A string describing the outcome: reference, new balance on success,
        or a human-readable error message on failure.
    """
    reference = _generate_reference()

    try:
        data = await ctx.context.banking_client.transfer(
            to_user_id=to_user_id,
            amount_ngn=amount_ngn,
            reference=reference,
            currency=currency,
        )

        tx = data.get("transaction", {})
        balance_after_ngn = kobo_to_ngn(data.get("senderBalanceAfter", 0))
        receiver_name = data.get("receiverUser", {}).get("name", to_user_id)

        return (
            f"Transfer successful.\n"
            f"Reference:        {tx.get('reference', reference)}\n"
            f"Amount:           ₦{amount_ngn:,.2f}\n"
            f"Recipient:        {receiver_name}\n"
            f"Status:           {tx.get('status', 'success')}\n"
            f"Your new balance: ₦{balance_after_ngn:,.2f}"
        )

    except BankingBackendError as exc:
        msg = exc.message.lower()

        if "insufficient" in msg or "balance" in msg:
            try:
                bal = await ctx.context.banking_client.get_balance(
                    user_id=ctx.context.user_id,
                    currency=currency,
                )
                current_ngn = kobo_to_ngn(bal.get("balance", 0))
                return (
                    f"Transfer failed: insufficient funds.\n"
                    f"Your current balance is ₦{current_ngn:,.2f}, "
                    f"but the transfer requires ₦{amount_ngn:,.2f}."
                )
            except BankingBackendError:
                pass  # fall through to generic message

        if "self" in msg:
            return "Transfer failed: you cannot send money to yourself."
        if "authentication" in msg or "401" in msg:
            return "Transfer failed: your session has expired. Please log in again."
        if "active" in msg or "403" in msg:
            return "Transfer failed: your account is not active. Please contact support."
        if "not found" in msg or "404" in msg:
            return f"Transfer failed: recipient '{to_user_id}' was not found on this platform."

        return f"Transfer failed: {exc.message}"
