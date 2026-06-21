# Pending Actions — Human-in-the-Loop Workflow

## What Are Pending Actions?

A pending action is a stored record that preserves the state of an in-progress
flow between separate voice requests. Because each voice message is a standalone
HTTP request, you have no memory of the previous turn unless it is injected as
context. Pending actions bridge this gap.

## When You Receive a Pending Actions Context Block

If the user's input begins with `[PENDING ACTIONS CONTEXT]`, it means the system
found active, unexpired pending actions for this user. Read the block carefully:

- **Action name** tells you what step was in progress.
- **Meta fields** contain the state saved from the previous turn (e.g. recipient
  account number, amount, currency).
- The **User message** at the bottom is what the user just said.

Treat the user message as a direct continuation of the pending flow unless the
user explicitly starts a different topic.

## Transfer Flow — Step-by-Step

### Request 1 (agent collects info and asks for confirmation)

1. Gather recipient account number, amount, and currency from the user's message.
2. If any piece is missing, ask for it — do NOT create a pending action yet.
3. Once you have all three, present the transfer summary to the user.
4. Call `create_pending_action` with:
   - `action_name`: `TRANSFER_AWAIT_CONFIRMATION`
   - `expires_in_minutes`: `5`
   - `meta`: `{ "to_account_number": "...", "amount_ngn": "...", "currency": "NGN" }`
5. Return the summary and ask: *"Shall I proceed? Say yes to confirm or no to cancel."*
6. Do NOT call `execute_transfer` yet.

### Request 2 (user confirms or cancels)

When you receive a `TRANSFER_AWAIT_CONFIRMATION` pending context:

**If the user confirms** (yes / proceed / go ahead / ok):
1. Call `execute_transfer` with the values from the pending action's meta.
2. Call `update_pending_action` with `status: "resolved"`.
3. Report the result.

**If the user cancels** (no / cancel / stop / abort):
1. Call `update_pending_action` with `status: "canceled"`.
2. Confirm the cancellation to the user.

**If the message is ambiguous** (e.g. the user changes the amount):
1. Update the pending action by calling `update_pending_action` with `status: "canceled"`.
2. Create a fresh `TRANSFER_AWAIT_CONFIRMATION` with the new values and ask for
   confirmation again.

## Rules

- Never execute a transfer without an explicit "yes" or equivalent from the user.
- If a pending action is expired, treat it as if it doesn't exist and start fresh.
- Always resolve or cancel a pending action once its flow concludes — never leave
  a resolved flow with a `pending` status.
- Pending actions are scoped to the authenticated user; never reference another
  user's pending actions.
