# BenefitBot — Requirements

## Project
BenefitBot helps rural users in India discover government schemes (central and state) they may
be eligible for, get a personalised document checklist, and receive the information in their
preferred language.

## Users
Primary: rural individuals in India with limited digital literacy.
Secondary: social workers or NGO volunteers helping beneficiaries.

## Functional requirements

1. The agent collects a user profile through natural conversation: state, age, occupation,
   income bracket, and category (farmer / woman / student / senior citizen / person with
   disability / general).
2. **Strands Decider 2B** selects which tool to call next (`search_central_schemes`,
   `search_state_schemes`, `search_both`, `ask_more_questions`) based on the profile
   collected so far. Pattern: `#tool-selection`.
3. When the decider confidence is below 0.6, the agent asks the user one more targeted
   question instead of calling a search tool.
4. The agent returns matched schemes with: name, brief description, eligibility summary,
   potential vs confirmed eligibility clearly distinguished, and a document checklist with
   application steps.
5. The user can switch response language at any time. Supported: English (default), Hindi,
   Tamil, Telugu, Bengali, Marathi.
6. AgentCore Memory stores the user profile across sessions so the user is not asked the
   same questions twice.

## Non-functional requirements

- All scheme data is synthetic JSON in `agent/data/`; deterministic for tests and the demo.
- No external API calls; offline-capable for the demo.
- Each decider call completes within 5 s on the AWSUGMDU hosted API.
- Scheme data clearly marks eligibility as "potential" (based on what the user said) vs
  "confirmed" (all criteria verified).
- Credit line "Built with the AWS User Group Madurai Strands Decider hackathon kit" is present
  in the README, the article footer, the demo app and the video end card.
