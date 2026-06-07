from enum import Enum

from pydantic import BaseModel


class IntentType(str, Enum):
    """
    Every voice command maps to exactly one of these intents.

    Using an Enum (not raw strings) means a typo anywhere in the codebase
    is a Python error at import time, not a silent bug at runtime.
    """

    CHECK_BALANCE = "check_balance"
    SEND_MONEY = "send_money"
    TRANSACTION_HISTORY = "transaction_history"
    BUY_AIRTIME = "buy_airtime"
    PAY_BILL = "pay_bill"
    UNKNOWN = "unknown"


class ParsedIntent(BaseModel):
    """
    What the LLM extracts from a transcript.

    We use OpenAI's structured output feature: instead of asking the LLM for
    free-form text and then parsing it ourselves, we hand it this Pydantic
    model as a schema and it fills the fields in directly. The result is always
    type-safe JSON — no regex, no fragile string parsing.

    All parameter fields are optional because they only apply to specific
    intents (e.g. `recipient` is only filled for send_money).
    """

    intent: IntentType
    confidence: float  # 0.0–1.0: how certain the model is

    # send_money
    recipient: str | None = None
    amount: float | None = None  # in Naira, numeric only
    note: str | None = None

    # buy_airtime
    phone_number: str | None = None

    # pay_bill
    bill_type: str | None = None  # "electricity", "water", "internet", etc.

    # check_balance
    account_type: str = "main"  # "main", "savings"

    # transaction_history
    transaction_limit: int | None = None
    days: int | None = None

    # one-sentence explanation of why the model chose this intent
    reasoning: str


class ToolResult(BaseModel):
    """
    What a tool returns after executing a banking operation.

    `data` holds the raw response from the NestJS banking backend.
    `message` is a human-readable summary we can show directly to the user.
    `requires_confirmation` is True for irreversible operations (like sending
    money) — the frontend can use this to show a confirm dialog before
    triggering the actual transfer.
    """

    success: bool
    data: dict | None = None
    message: str
    requires_confirmation: bool = False


class OperationResponse(BaseModel):
    """
    The full response returned by POST /api/v1/operations/process-voice-operation.

    Includes everything the frontend needs to render a result:
    - what the user said (transcript)
    - what we understood (intent + confidence)
    - what parameters we extracted (e.g. amount, recipient)
    - what the banking backend returned (result)
    """

    transcript: str
    intent: IntentType
    confidence: float
    parameters: dict
    result: ToolResult
