"""
Balance Agent — specialist for account balance and wallet inquiries.
"""

from agents import Agent

from app.agents.base import RequestContext, build_agent_instructions, get_litellm_model
from app.tools.balance_tools import get_all_wallets, get_wallet_balance

_instructions = build_agent_instructions(
    ("agents", "balance_agent.md"),
    ("workflows", "balance_check.md"),
    ("core", "compliance.md"),
    ("core", "security.md"),
)

balance_agent: Agent[RequestContext] = Agent(
    name="Balance_Agent",
    instructions=_instructions,
    tools=[get_wallet_balance, get_all_wallets],
    model=get_litellm_model(),
)
