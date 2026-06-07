"""
Balance tools — callable by the Balance_Agent.

These tools call the NestJS banking backend to fetch wallet balance information
for the authenticated user. All amounts returned from the API are in kobo;
we convert to NGN before returning the result string.
"""

from agents import RunContextWrapper, function_tool

from app.agents.base import RequestContext
from app.core.exceptions import BankingBackendError
from app.integrations.banking.client import kobo_to_ngn


@function_tool
async def get_wallet_balance(
    ctx: RunContextWrapper[RequestContext],
    currency: str = "NGN",
) -> str:
    """
    Get the authenticated user's balance for a specific currency wallet.

    Args:
        currency: 3-letter ISO currency code (default: NGN).

    Returns:
        A formatted string with the wallet balance, or an error message.
    """
    try:
        data = await ctx.context.banking_client.get_balance(
            user_id=ctx.context.user_id,
            currency=currency,
        )
        balance_ngn = kobo_to_ngn(data.get("balance", 0))
        return (
            f"Balance retrieved.\n"
            f"Currency: {currency.upper()}\n"
            f"Balance: ₦{balance_ngn:,.2f}\n"
            f"Wallet ID: {data.get('walletId', '')}"
        )
    except BankingBackendError as exc:
        return f"Could not retrieve balance: {exc.message}"


@function_tool
async def get_all_wallets(ctx: RunContextWrapper[RequestContext]) -> str:
    """
    Get all wallets and their balances for the authenticated user.

    Returns a list of every currency wallet the user holds, with balances
    converted from kobo to NGN.
    """
    try:
        data = await ctx.context.banking_client.get_all_wallets()
        wallets = data if isinstance(data, list) else data.get("wallets", [])

        if not wallets:
            return "You have no wallets yet."

        lines = ["Your wallets:"]
        for w in wallets:
            currency = w.get("currency", "?")
            balance_ngn = kobo_to_ngn(w.get("balance", 0))
            lines.append(f"  {currency}: ₦{balance_ngn:,.2f}")

        return "\n".join(lines)
    except BankingBackendError as exc:
        return f"Could not retrieve wallets: {exc.message}"
