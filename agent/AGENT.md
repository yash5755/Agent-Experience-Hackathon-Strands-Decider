# Use case

- **Pitch:** BenefitBot helps rural Indians discover government schemes they may be eligible for,
  get a personalised document checklist, and receive everything in their preferred language.
- **Who it is for:** Rural individuals in India with limited digital literacy, and social workers
  or NGO volunteers helping beneficiaries navigate central and state government schemes.
- **Features:**
  - asks the user a few conversational questions to build a profile (state, age, occupation,
    income, category);
  - Strands Decider 2B picks the right search tool for each profile — central schemes, state
    schemes, both, or "ask one more question" — before the LLM turn;
  - returns matched schemes with potential vs confirmed eligibility clearly distinguished;
  - generates a personalised document checklist and application guide per scheme;
  - responds in the user's preferred language (English default; Hindi, Tamil, Telugu, Bengali,
    Marathi on request);
  - deployed on Amazon Bedrock AgentCore Runtime with Memory so the profile is remembered
    across sessions.
- **The decision handed to Strands Decider 2B:** given the user profile collected so far, which
  tool should handle this request — search central schemes, search state schemes, search both,
  or ask the user one more clarifying question? (`#tool-selection`)
- **Why a decision model:** the tool selection runs on every turn; it must be fast, cheap and
  correct. A specialised 2B model is far cheaper and faster than asking the full LLM to pick.
- **Amazon Bedrock:** the conversation and tool use (Amazon Nova Pro on deployment).
