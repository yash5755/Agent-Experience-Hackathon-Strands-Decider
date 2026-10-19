"""REUSABLE DECISION PATTERN: scheme tool selection  (#tool-selection)

What it does
    Before BenefitBot searches for Indian government schemes, Strands Decider 2B reads the
    user's profile collected so far and picks which tool to call:

        search_schemes       — the user's state is known; search central + state schemes now
        ask_more_questions   — key profile fields (especially state) are missing; ask first

    This single binary decision keeps the choice sharp and the decider confident. When
    confidence is below the threshold (0.6), all tools are kept and the LLM decides,
    so no opportunity is lost.

Typed questions and options
    `tool` (choice): built from the two tools' docstrings by `questions_for()` from
    `decider_kit.patterns.tool_selection`, plus `none` (answer directly).

Wiring (where it sits in the agent's path)
    Between the user message and the Strands Agent:

        from agent.decision import selector_for
        selector = selector_for(decider)
        narrowed_tools = selector.tools_for(user_message, history=conversation_history)
        agent = Agent(model=..., tools=narrowed_tools + [get_document_checklist, get_user_profile])
        result = agent(user_message)

How to reuse it in your own agent
    1. Replace search_schemes and ask_more_questions with your own tools.
    2. Give every tool a clear one-line docstring: that line becomes the option the decider
       reads when picking.
    3. Adjust the `context` hint in `selector_for` to describe your domain.
    4. Tune `threshold` (default 0.6): lower → LLM decides more often; higher → decider
       narrows more aggressively.
    5. Keep the state sent to the decider short and factual — no LLM-invented inferences.
"""

from __future__ import annotations

from decider_kit import Decider
from decider_kit.patterns.tool_selection import ToolSelector, questions_for

PATTERN_TAG = "#tool-selection"

# Exposed for ./kit bench (imported before tools module is fully loaded at runtime).
QUESTIONS = {
    "tool": Decider.choice(
        "Given the user profile, which tool should the agent call next?",
        {
            "search_schemes": (
                "the user's state IS known — search central and state government schemes now"
            ),
            "ask_more_questions": (
                "the user's state is unknown OR key profile fields are missing — "
                "ask the user one clarifying question before searching"
            ),
            "none": "no tool needed; the agent can answer directly",
        },
    )
}


def selector_for(decider: Decider, threshold: float = 0.6) -> ToolSelector:
    """Return a ToolSelector wired to BenefitBot's two routing tools."""
    from .tools import ask_more_questions, search_schemes

    return ToolSelector(
        decider,
        tools=[search_schemes, ask_more_questions],
        threshold=threshold,
        context=(
            "The user is asking about Indian government benefit schemes. "
            "Use search_schemes when the user has mentioned their state. "
            "Use ask_more_questions when state is unknown or missing."
        ),
    )
