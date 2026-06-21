"""
Transfer Agent — specialist for money transfers between platform users.
"""

from agents import Agent

from app.agents.base import RequestContext, build_agent_instructions, get_litellm_model
from app.tools.pending_action_tools import create_pending_action, update_pending_action
from app.tools.transfer_tools import execute_transfer, verify_account_number

_instructions = build_agent_instructions(
    ("agents", "transfer_agent.md"),
    ("workflows", "transfer.md"),
    ("workflows", "pending_actions.md"),
    ("core", "compliance.md"),
    ("core", "security.md"),
)

transfer_agent: Agent[RequestContext] = Agent(
    name="Transfer_Agent",
    instructions=_instructions,
    tools=[verify_account_number, execute_transfer, create_pending_action, update_pending_action],
    model=get_litellm_model(),
)
