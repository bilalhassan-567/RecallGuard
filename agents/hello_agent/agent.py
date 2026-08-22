"""Phase 1 hello-world agent — confirms the ADK + Gemini wiring works locally before
any real recall/matching logic gets built on top of it."""
from google.adk.agents import Agent

import config

root_agent = Agent(
    name="hello_agent",
    model=config.GEMINI_MODEL,
    description="A minimal agent that verifies the ADK + Gemini setup is working.",
    instruction=(
        "You are a test agent for the RecallGuard project. When greeted, respond in one "
        "short sentence confirming you're operational, and name the model you're running on."
    ),
)
