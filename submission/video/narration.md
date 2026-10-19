0. BenefitBot helps rural users in India find government schemes. Strands Decider picks the right search tool — central schemes, state schemes, or ask a clarifying question — before each agent turn.

1. BenefitBot helps rural Indians discover government schemes they may be eligible for, with a personalised document checklist, in their own language. What it does: Asks a few questions to understand the user's profile. Strands Decider picks the right scheme search tool before every LLM turn. Returns matched central and state schemes with POTENTIAL vs confirmed eligibility. Generates a personalised document checklist and application guide.

2. A user opens BenefitBot with no profile yet — the decider should route to ask_more_questions. The decider scored confidence 0.43, so the verdict was ask_more_questions, in 2.1 seconds.

3. Profile is now rich enough — the decider should route to search_both or search_state_schemes. The decider scored confidence 0.66, so the verdict was search_schemes, in 2.3 seconds.

4. User asks for a specific scheme checklist — get_document_checklist is called. The decider scored confidence 0.85, so the verdict was search_schemes, in 2.7 seconds.

5. User switches language to Tamil mid-conversation. The decider scored confidence 0.70, so the verdict was search_schemes, in 3.4 seconds.

6. On 14 labelled decisions, with the decider on the AWS Student Builder Group VVCE hosted API, Strands Decider was 93% accurate at a median of 1878 milliseconds, against 100% and 11200 milliseconds for a hosted open LLM asked the same questions.

7. One Strands Decider call per turn selects the right tool. The LLM handles only what it is good at — talking to the user and composing the answer.