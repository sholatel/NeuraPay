"""
Transactions Agent — specialist for transaction history and ledger inquiries.
"""

from agents import Agent

from app.agents.base import RequestContext, build_agent_instructions, get_litellm_model
from app.tools.transaction_tools import get_transaction_history

_instructions = build_agent_instructions(
    ("agents", "transactions_agent.md"),
    ("core", "compliance.md"),
    ("core", "security.md"),
)

transactions_agent: Agent[RequestContext] = Agent(
    name="Transactions_Agent",
    instructions=_instructions,
    tools=[get_transaction_history],
    model=get_litellm_model(),
)
