"""
Transfer tools — callable by the Transfer_Agent.

Handles recipient verification and execution of money transfers.
The agent must verify the recipient name and get explicit user confirmation
before calling execute_transfer.
"""

import uuid

from agents import RunContextWrapper, function_tool

from app.agents.base import RequestContext
from app.core.exceptions import BankingBackendError


def _generate_reference() -> str:
    """Generate a unique transaction reference for the banking backend.

    Format: AI-<16 uppercase hex chars>
    Satisfies the backend constraint: unique, 8–100 chars.
    """
    return f"AI-{uuid.uuid4().hex[:16].upper()}"


@function_tool
async def verify_account_number(
    ctx: RunContextWrapper[RequestContext],
    account_number: str,
) -> str:
    """
    Look up a recipient's account number and return their basic details.

    Always call this before showing a transfer summary — the user must see
    and confirm the recipient's name, not just the account number.

    Args:
        account_number: The recipient's 10-digit NUBAN account number.

    Returns:
        Recipient name, account number, and bank on success, or a clear
        error message if the account is not found.
    """
    try:
        data = await ctx.context.banking_client.lookup_account(account_number)
        name = data.get("name", "Unknown")
        bank = data.get("bank", "NeuraPay")
        email = data.get("email", "")
        return (
            f"Account found.\n"
            f"Name:           {name}\n"
            f"Account Number: {account_number}\n"
            f"Bank:           {bank}\n"
            f"Email:          {email}"
        )
    except BankingBackendError as exc:
        msg = exc.message.lower()
        if "not found" in msg or "404" in str(exc.detail or ""):
            return (
                f"No account found with number '{account_number}'. "
                "Please ask the user to double-check the account number."
            )
        return f"Could not verify account: {exc.message}"


@function_tool
async def execute_transfer(
    ctx: RunContextWrapper[RequestContext],
    to_account_number: str,
    amount_ngn: float,
    currency: str = "NGN",
) -> str:
    """
    Execute a money transfer from the authenticated user to another platform user.

    IMPORTANT: Only call this after the user has explicitly confirmed the
    transfer summary. Show the recipient account number, amount, and currency
    first and ask for confirmation before invoking this tool.

    Args:
        to_account_number: The recipient's 10-digit NUBAN account number (e.g. 9990000014).
        amount_ngn:         Amount to transfer in Nigerian Naira (e.g. 5000 for ₦5,000).
        currency:           Currency code, defaults to NGN.

    Returns:
        A string describing the outcome: reference, new balance on success,
        or a human-readable error message on failure.
    """
    reference = _generate_reference()

    try:
        data = await ctx.context.banking_client.transfer(
            to_account_number=to_account_number,
            amount_ngn=amount_ngn,
            reference=reference,
            currency=currency,
        )

        tx = data.get("transaction", {})
        balance_after_ngn = float(data.get("senderBalanceAfter", 0))
        receiver_name = data.get("receiverUser", {}).get("name", to_account_number)

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
                current_ngn = float(bal.get("balance", 0))
                return (
                    f"Transfer failed: insufficient funds.\n"
                    f"Your current balance is ₦{current_ngn:,.2f}, "
                    f"but the transfer requires ₦{amount_ngn:,.2f}."
                )
            except BankingBackendError:
                pass

        if "self" in msg:
            return "Transfer failed: you cannot send money to yourself."
        if "authentication" in msg or "401" in msg:
            return "Transfer failed: your session has expired. Please log in again."
        if "active" in msg or "403" in msg:
            return "Transfer failed: your account is not active. Please contact support."
        if "not found" in msg or "404" in msg:
            return f"Transfer failed: account number '{to_account_number}' was not found on this platform."

        return f"Transfer failed: {exc.message}"
