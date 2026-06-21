"""
Fixed constants for pending action names.

These are plain string constants (not a DB enum) so new action names can be
added without a schema migration. The status column is the only enum field.
"""


class PendingActionName:
    # Transfer flow — multi-step confirmation loop
    TRANSFER_CONFIRM_RECIPIENT = "TRANSFER_CONFIRM_RECIPIENT"
    TRANSFER_CONFIRM_AMOUNT = "TRANSFER_CONFIRM_AMOUNT"
    TRANSFER_AWAIT_CONFIRMATION = "TRANSFER_AWAIT_CONFIRMATION"

    ALL: frozenset[str] = frozenset(
        {
            TRANSFER_CONFIRM_RECIPIENT,
            TRANSFER_CONFIRM_AMOUNT,
            TRANSFER_AWAIT_CONFIRMATION,
        }
    )
