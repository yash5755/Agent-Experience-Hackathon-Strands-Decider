# BenefitBot — Design

## Architecture

```
User message
    │
    ▼
HackathonAgent.chat()
    │
    ├─ ToolSelector.tools_for(message, history)   ← Strands Decider 2B (#tool-selection)
    │       decides: search_central_schemes | search_state_schemes
    │               search_both | ask_more_questions
    │       confidence < 0.6 → returns [ask_more_questions] only
    │
    ▼
Strands Agent (qwen3.5-4b / Amazon Nova Pro on deploy)
    │   system prompt: profile collector + language instruction
    │   tools: only what the decider selected
    │
    ├─ get_user_profile()          collect / update profile fields
    ├─ search_central_schemes()    filter central_schemes.json by profile
    ├─ search_state_schemes()      filter state_schemes.json by profile
    ├─ search_both()               call both and merge
    ├─ ask_more_questions()        return a targeted clarifying question
    └─ get_document_checklist()    return docs + steps for a scheme slug
    │
    ▼
reply dict: reply, decisions, model_id, latency_ms
```

## Decision wiring (`decision.py`)

Pattern: `#tool-selection` using `decider_kit.patterns.tool_selection.ToolSelector`.

State sent to decider:
```
User profile so far:
  state: <state or unknown>
  age: <age or unknown>
  occupation: <occupation or unknown>
  income: <income or unknown>
  category: <category or unknown>

User message: <latest message>
```

Questions:
```python
QUESTIONS = questions_for([
    search_central_schemes,
    search_state_schemes,
    search_both,
    ask_more_questions,
])
```
`ToolSelector` builds questions from each tool's docstring automatically.

Threshold: 0.6. Below that, all tools are returned and the LLM decides (safe fallback).

## Data (`agent/data/`)

- `central_schemes.json` — 20 central government schemes
- `state_schemes.json`   — 20 state government schemes (4–5 states: TN, MH, WB, UP, KA)

Each scheme record:
```json
{
  "slug": "pm-kisan",
  "name": "PM-KISAN",
  "full_name": "Pradhan Mantri Kisan Samman Nidhi",
  "level": "central",
  "state": null,
  "category": ["farmer"],
  "min_age": 18,
  "max_age": null,
  "max_income_lpa": 2.0,
  "description": "...",
  "benefit": "...",
  "eligibility_criteria": ["..."],
  "documents": ["..."],
  "application_steps": ["..."],
  "apply_url": "..."
}
```

## Language

The system prompt instructs the LLM to reply in `LANGUAGE` (an env var the agent sets per
session based on what the user requests). Supported values: `english`, `hindi`, `tamil`,
`telugu`, `bengali`, `marathi`. Default: `english`.

## AgentCore features

- Memory: enabled (SEMANTIC + USER_PREFERENCE), stores user profile across sessions.
- Gateway: disabled.

## Files changed

```
agent/AGENT.md           ← replaced
agent/decision.py        ← replaced (ToolSelector wiring)
agent/tools.py           ← replaced (5 tools)
agent/agent.py           ← replaced (HackathonAgent with ToolSelector)
agent/eval_cases.jsonl   ← replaced (≥24 cases)
agent/demo_script.yaml   ← replaced
agent/features.yaml      ← replaced (memory: true)
agent/data/central_schemes.json  ← new
agent/data/state_schemes.json    ← new
.kiro/specs/benefitbot/  ← this spec
```
