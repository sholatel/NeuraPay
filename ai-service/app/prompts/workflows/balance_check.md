# Balance Check Workflow

## Standard Flow

1. Call `get_wallet_balance` with `currency="NGN"` (or the currency the user specifies).
2. Present the balance clearly:
   ```
   Your NGN wallet balance is ₦15,000.00
   ```
3. If the user asks about all wallets / all currencies, call `get_all_wallets` instead
   and present each wallet's balance in a structured list.

## Display Rules

- Always format amounts with comma separators and two decimal places: ₦1,500,000.00
- Always include the currency symbol (₦ for NGN).
- If balance is zero: "Your NGN wallet has a zero balance."
- If the wallet doesn't exist for the requested currency: inform the user and list the
  currencies they do have wallets for.

## Context Awareness

- If the user asks "what can I afford?" or "can I send X?", check the balance and
  compare it to the requested amount, then answer the question directly.
- If the user just asked about a transfer and it failed due to insufficient funds,
  offer to show the balance immediately to help them understand the shortfall.
