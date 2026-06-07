# Transfer Workflow

This document defines the exact workflow for processing money transfer requests.
Follow these steps in order every time.

## Step 1 — Gather Required Information

A transfer requires three pieces of information:
1. **Recipient** — the recipient's User ID (UUID) or email address
2. **Amount** — in Nigerian Naira (₦), must be a positive integer
3. **Currency** — defaults to NGN unless the user specifies otherwise

If any of these are missing from the voice command, ask the user for the missing
information before proceeding. Ask for one missing piece at a time.

**Important:** The platform identifies recipients by User ID (UUID). If the user provides
a name (e.g., "send to John"), you must ask: *"Please provide John's User ID or email
address so I can complete the transfer."* Do not guess or fabricate a recipient ID.

## Step 2 — Show Transfer Summary

Before executing the transfer, always show a clear summary:

```
Transfer Summary
----------------
To:       [Recipient ID or identifier]
Amount:   ₦[amount formatted with commas]
Currency: NGN
```

Then ask: *"Shall I proceed with this transfer?"*

If the user confirms (yes, proceed, ok, go ahead), proceed to Step 3.
If the user cancels or says no, cancel the transfer and confirm cancellation.

## Step 3 — Execute Transfer

Call the `execute_transfer` tool with the confirmed parameters.
A unique transaction reference is generated automatically.

## Step 4 — Confirm Result

On success, present:
- Confirmation message with the transaction reference
- Remaining balance after the transfer
- Fraud awareness note for first-time recipients or large amounts

On failure, present:
- A clear explanation of why it failed (insufficient funds, invalid recipient, etc.)
- Suggested next steps

## Limits & Edge Cases

- Minimum transfer: ₦1
- The sender cannot transfer to themselves — inform the user and ask for the correct
  recipient if this occurs.
- Insufficient funds: show the current balance and the shortfall.
- Account not opened: direct the user to contact support.
