"""BenefitBot: find Indian government schemes you may be eligible for, in your language.

Strands Decider 2B (#tool-selection) picks which tool to call — search central schemes,
search state schemes, search both, or ask the user a clarifying question — before every
agent turn. This keeps the LLM focused and the per-turn cost low.

    from agent.agent import HackathonAgent
    out = HackathonAgent().chat("I am a farmer in Tamil Nadu, age 45, income 1.5 lakh")
    out["reply"], out["decisions"]
"""

from __future__ import annotations

import time
from typing import Any

from strands import Agent

from decider_kit import Decider
from decider_kit.llm import agent_model, default_model_id, strip_thinking

from .decision import selector_for
from .tools import TOOLS

NAME = "BenefitBot"

SYSTEM_PROMPT = """You are BenefitBot, a helpful assistant that helps people in India discover
government schemes they may be eligible for. You serve rural users who may have limited
digital literacy. Be warm, simple and clear.

Your job in each turn:
1. If you don't know the user's state, age, category (farmer/woman/student/senior/disabled/general)
   and rough income, ask one or two questions at a time using ask_more_questions.
2. Once you have enough profile details, use the search tools to find matching schemes.
3. Present matched schemes clearly: name, benefit, and whether eligibility is POTENTIAL or
   needs more verification. Never claim confirmed eligibility — only say "you may be eligible".
4. When the user asks for details on a specific scheme, call get_document_checklist immediately
   with the scheme's slug (e.g. "pm-kisan"). Never ask for extra information before calling it.
5. If the user asks to change language (e.g. "Hindi mein batao", "Tamil la sollu", "Kannada alli heli"), respond
   in that language from that point onwards. Supported: English, Hindi, Tamil, Telugu,
   Bengali, Marathi, Kannada.
6. Always distinguish: POTENTIAL eligibility (based on what they told you) vs official
   confirmation (which only happens at the application stage).
7. Keep replies short and readable. Use bullet points for document lists.

Always be warm, patient and helpful.

Built with the AWS Student Builder Group VVCE Strands Decider hackathon kit."""


class HackathonAgent:
    """BenefitBot with Strands Decider 2B tool selection wired in."""

    def __init__(
        self,
        decider: Decider | None = None,
        model_id: str | None = None,
        eager: bool | None = None,
    ):
        self.decider = decider or Decider()
        self.model_id = model_id or default_model_id()
        self.sessions: dict[str, dict[str, Any]] = {}

    def _session(self, session_id: str) -> dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "history": [],   # list of "role: message" strings for decider context
                "agent": None,   # Strands Agent (recreated per turn with narrowed tools)
                "selector": selector_for(self.decider),
                "decision_log": [],
            }
        return self.sessions[session_id]

    def chat(
        self,
        message: str,
        session_id: str = "default",
        images: list[Any] | None = None,
    ) -> dict[str, Any]:
        sess = self._session(session_id)
        selector = sess["selector"]
        history = "\n".join(sess["history"][-10:])  # last 5 turns for context

        # --- Strands Decider 2B picks the tools ---
        narrowed_tools = selector.tools_for(message, history=history)

        # get_document_checklist and get_user_profile are always available; the decider
        # only routes between search_schemes and ask_more_questions.
        from .tools import get_document_checklist, get_user_profile

        tool_set = list(narrowed_tools)
        for always_on in [get_user_profile, get_document_checklist]:
            if always_on not in tool_set:
                tool_set.append(always_on)

        # Build a fresh agent with narrowed tool set for this turn
        agent = Agent(
            model=agent_model(self.model_id),
            system_prompt=SYSTEM_PROMPT,
            tools=tool_set,
            callback_handler=None,
        )

        t0 = time.perf_counter()
        result = agent(message)
        latency_ms = round((time.perf_counter() - t0) * 1000)
        reply = strip_thinking(str(result))

        # Record history for next turn's decider context
        sess["history"].append(f"User: {message}")
        sess["history"].append(f"BenefitBot: {reply[:200]}")

        # Collect decision log from selector
        new_decisions = selector.log[len(sess["decision_log"]):]
        sess["decision_log"].extend(new_decisions)

        # Normalise decision dicts to kit contract: probabilities 0..1, verdict, decider_ms
        decisions_out = []
        for d in new_decisions:
            decisions_out.append({
                "pattern": "#tool-selection",
                "tool_selected": d.get("tool"),
                "confidence": d.get("confidence", 0.0),
                "narrowed": d.get("narrowed", False),
                "probabilities": d.get("probabilities", {}),
                "verdict": d.get("tool", "none"),
                "decider_ms": d.get("decider_ms", 0),
            })

        return {
            "reply": reply,
            "decisions": decisions_out,
            "model_id": self.model_id,
            "latency_ms": latency_ms,
            "agent": NAME,
        }


if __name__ == "__main__":
    import json
    import sys

    a = HackathonAgent()
    msgs = sys.argv[1:] or [
        "Hello, I need help finding government schemes.",
        "I am a farmer in Tamil Nadu, 45 years old, income about 1.5 lakh per year.",
        "Show me the checklist for pm-kisan please.",
    ]
    for msg in msgs:
        print(f"\nUser: {msg}")
        out = a.chat(msg)
        print(f"BenefitBot: {out['reply']}")
        if out["decisions"]:
            d = out["decisions"][0]
            print(f"[Decider: {d['tool_selected']} confidence={d['confidence']:.2f} {d['decider_ms']}ms]")
