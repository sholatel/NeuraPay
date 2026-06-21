# Transfer Workflow

This document defines the exact workflow for processing money transfer requests.
Follow these steps in order every time.

## Step 1 — Gather Required Information

A transfer requires three pieces of information:
1. **Recipient** — the recipient's 10-digit NUBAN account number (e.g. `9990000014`)
2. **Amount** — in Nigerian Naira (₦), must be a positive integer
3. **Currency** — defaults to NGN unless the user specifies otherwise

If any of these are missing from the voice command, ask for the missing piece before
moving on. Ask for one piece at a time.

**Important:** The platform identifies recipients by their **10-digit account number**.
If the user provides a name (e.g., "send to John"), you must ask:
*"Please provide John's 10-digit account number so I can complete the transfer."*
Do not guess or fabricate an account number.

## Step 2 — Verify the Recipient (Name Check)

Once you have the account number, call `verify_account_number` before doing anything else.

- If the account **exists**: you will receive the recipient's name, bank, and email.
  Present this to the user:
  > *"I found **[Name]** on NeuraPay (account ending ...XXXX). Is this the right person?"*
  Do not proceed until the user confirms the name is correct.
  If the user says the name is wrong, ask them to recheck the account number.

- If the account **does not exist**: tell the user the account number was not found and
  ask them to double-check. Do not proceed.

## Step 3 — Show Transfer Summary & Save Pending Action

Once the user has confirmed the recipient's name, show a full transfer summary:

```
Transfer Summary
----------------
To:     [Recipient Name] — [Account Number] (NeuraPay)
Amount: ₦[amount formatted with commas]
```

Then call `create_pending_action` with:
- `action_name`: `TRANSFER_AWAIT_CONFIRMATION`
- `expires_in_minutes`: `5`
- `meta`: `{ "to_account_number": "...", "amount_ngn": "...", "recipient_name": "...", "currency": "NGN" }`

Then ask: *"Shall I proceed? Say yes to confirm or no to cancel."*
Stop here — wait for the user's next voice message. Do NOT call `execute_transfer` yet.

## Step 4 — Execute Transfer (next voice request)

On the next request, if a `TRANSFER_AWAIT_CONFIRMATION` pending action is present:

**If the user confirms** (yes / proceed / go ahead / ok):
1. Call `execute_transfer` using the values from the pending action's meta.
2. Call `update_pending_action` with `status: "resolved"`.
3. Report the result (reference, new balance).

**If the user cancels** (no / cancel / stop):
1. Call `update_pending_action` with `status: "canceled"`.
2. Confirm the cancellation.

**If the user changes a detail** (different amount, different recipient):
1. Cancel the old pending action: `update_pending_action(status: "canceled")`.
2. Restart from Step 1 with the new details.

## Step 5 — Confirm Result

On success, present:
- Confirmation message with the transaction reference
- Recipient name and account number
- Remaining balance after the transfer
- Fraud awareness note for large amounts (above ₦100,000)

On failure, present:
- A clear human-friendly explanation (insufficient funds, invalid account, etc.)
- Suggested next steps

## Limits & Edge Cases

- Minimum transfer: ₦1
- The sender cannot transfer to themselves — inform the user and ask for a different recipient.
- Insufficient funds: show the current balance and the shortfall.
- Account not opened: direct the user to contact support.
