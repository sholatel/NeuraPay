"""
Transaction tools — callable by the Transactions_Agent.

Fetches paginated ledger history for the authenticated user and formats
it into a readable summary. Amounts from the API are in NGN.
"""

from agents import RunContextWrapper, function_tool

from app.agents.base import RequestContext
from app.core.exceptions import BankingBackendError


def _direction_icon(direction: str) -> str:
    return "↑" if direction == "incoming" else "↓"


def _signed_amount(amount_ngn: float, direction: str) -> str:
    prefix = "+" if direction == "incoming" else "-"
    return f"{prefix}₦{abs(amount_ngn):,.2f}"


def _shorten_id(uid: str | None) -> str:
    """Truncate a UUID to the first 8 chars for display readability."""
    if not uid:
        return "—"
    return uid[:8] + "…"


@function_tool
async def get_transaction_history(
    ctx: RunContextWrapper[RequestContext],
    currency: str = "NGN",
    limit: int = 10,
    page: int = 1,
) -> str:
    """
    Get the authenticated user's transaction history from the ledger.

    Transactions are returned newest-first. Each entry shows direction
    (↑ incoming / ↓ outgoing), amount, type, reference, and date.

    Args:
        currency: Currency to filter by (default: NGN).
        limit:    Number of transactions per page (1–100, default 10).
        page:     Page number for pagination (default 1).

    Returns:
        A formatted list of transactions, or a message if none exist.
    """
    try:
        data = await ctx.context.banking_client.get_transactions(
            currency=currency,
            page=page,
            limit=limit,
        )

        entries = data.get("data", [])
        meta = data.get("meta", {})
        total = meta.get("total", len(entries))

        if not entries:
            return (
                f"You have no {currency} transactions yet. "
                "Make your first deposit or transfer to get started."
            )

        lines = [f"Your last {len(entries)} of {total} {currency} transactions:\n"]

        for entry in entries:
            direction = entry.get("direction", "outgoing")
            amount_ngn = float(entry.get("amount", 0))
            tx_type = entry.get("type", "transfer").capitalize()
            status = entry.get("status", "success")
            reference = entry.get("reference", "")
            counterparty = _shorten_id(entry.get("counterpartyUserId"))
            date = entry.get("createdAt", "")[:10]

            icon = _direction_icon(direction)
            amount_str = _signed_amount(amount_ngn, direction)
            cp_str = f" | {counterparty}" if counterparty != "—" else ""

            lines.append(
                f"{icon} {amount_str} — {tx_type}{cp_str} "
                f"(Ref: {reference[:12]}…) [{status}] — {date}"
            )

        total_pages = meta.get("totalPages", 1)
        if total_pages > page:
            lines.append(
                f"\n(Page {page}/{total_pages} — ask for 'next page' to see more)"
            )

        return "\n".join(lines)

    except BankingBackendError as exc:
        return f"Could not retrieve transaction history: {exc.message}"
