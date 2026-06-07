"""
Banking Agent — the top-level triage agent.

Responsibilities:
  - Understand the user's intent from natural language.
  - Delegate to the appropriate specialist via handoff.
  - Never execute financial operations directly.

Architecture note:
  Specialist agents are imported and referenced in `handoffs`. When the Banking
  Agent calls handoff(balance_agent), the Agents SDK runtime transfers the full
  conversation context to the Balance Agent, which then calls its tools and
  returns the result. The Banking Agent never sees the raw tool output.
"""

from agents import Agent, handoff

from app.agents.base import RequestContext, build_agent_instructions, get_litellm_model
from app.agents.specialists.balance_agent import balance_agent
from app.agents.specialists.transactions_agent import transactions_agent
from app.agents.specialists.transfer_agent import transfer_agent

_instructions = build_agent_instructions(
    ("agents", "banking_agent.md"),
    ("core", "compliance.md"),
    ("core", "security.md"),
)

banking_agent: Agent[RequestContext] = Agent(
    name="Banking_Agent",
    instructions=_instructions,
    handoffs=[
        handoff(balance_agent),
        handoff(transfer_agent),
        handoff(transactions_agent),
    ],
    model=get_litellm_model(),
)
