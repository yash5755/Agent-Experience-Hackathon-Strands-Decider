# Bridging the 1.4 Billion Citizen Divide: How BenefitBot Uses Strands Decider 2B and Amazon Bedrock to Democratize Indian Welfare Schemes

By Vivek and Team

India is home to over 1.4 billion (140+ crore) citizens. Every year, the central government and 28 state administrations allocate hundreds of thousands of crores to welfare programs: direct farmer income support through PM-Kisan, free health coverage under Ayushman Bharat, rural employment via MGNREGA, housing under PMAY, and specialized state subsidies like Karnataka's Raitha Siri or Tamil Nadu's agricultural assistance.

Yet, ask an ordinary citizen in a rural village, and a painful paradox emerges: with hundreds of schemes funded and active, how many people actually receive their benefits? Why is not everyone utilizing them?

The truth is that the bottleneck is no longer policy or funding -- it is accessibility. Millions of eligible families remain excluded because of three massive hurdles:

1. Portal Fragmentation: Information is scattered across hundreds of isolated departmental websites, each with its own rigid terminology and navigation.
2. The Language and Literacy Barrier: Over 70% of welfare-eligible citizens speak regional languages like Tamil, Telugu, Kannada, Bengali, or Marathi. Most online government portals default to complex administrative English or formal Hindi, leaving rural beneficiaries stranded.
3. Paperwork Anxiety: Countless citizens travel miles to government offices only to be rejected because they did not know they needed a specific land record (RTC), caste certificate, or income affidavit.

BenefitBot was created to dismantle these barriers. It is a conversational assistant built on Amazon Bedrock AgentCore Runtime that speaks to citizens in their native language, asks a few gentle clarifying questions, matches them against central and state scheme databases, and produces concrete, personalized document checklists. 

Behind the scenes, BenefitBot pairs Strands Decider 2B with Amazon Bedrock: the decider handles lightning-fast, deterministic tool routing, while Bedrock delivers empathetic, clear conversational guidance.

## The project

BenefitBot is designed for rural beneficiaries, smallholder farmers, women entrepreneurs, students, and the social workers and Common Service Centre (CSC) operators who assist them. 

Key capabilities include:
- Conversational Profile Building: Rather than forcing users through 50-field forms, the agent converses naturally, extracting key factors like state, age, category, landholding, and income.
- Intelligent Tool Routing with Strands Decider 2B: On every single turn, before invoking the generative LLM, Strands Decider evaluates whether enough profile data exists. If details are missing, it routes to ask clarifying questions; once the state is established, it triggers targeted scheme database lookups.
- Potential vs Confirmed Eligibility: BenefitBot never gives false guarantees. It clearly labels eligibility as potential based on conversational disclosures and highlights exact verification criteria.
- Personalized Document Guides: When a user selects a scheme, BenefitBot lists the exact paperwork required (Aadhaar, bank passbook, land records) so citizens never make unnecessary trips to bureaucratic offices.
- Multilingual Fluidity: Responds seamlessly in regional languages including Hindi, Tamil, Telugu, Kannada, Marathi, and Bengali.
- Persistent Session Memory: Hosted on Amazon Bedrock AgentCore Runtime with AgentCore Memory, allowing a citizen or volunteer to return days later without repeating their life story.

Here is a real interaction:

User: "I am a farmer from Tamil Nadu. I am 45 years old and my income is about 1.5 lakh per year. What schemes can help me?"
BenefitBot: "Based on your farming background in Tamil Nadu, you may be potentially eligible for:
1. PM-Kisan Samman Nidhi: Central scheme providing Rs 6,000 per year direct income support.
2. Tamil Nadu Chief Minister's Uzhavar Pathukappu Thittam: Comprehensive social security for farmers.
Would you like me to generate the exact document checklist you need to apply for PM-Kisan?"

User: "Tamil la sollu"
BenefitBot: "Nandri! PM-Kisan thittathukku neengal thaguthiyudaiyavargalaga irukkalam. Idharku thevaiyana aavanangal: 1. Aadhaar card, 2. Nilam pathira aavanam (Chitta/Patta), 3. Vangi kanaku puthagam (Bank Passbook). Melum vivarangal thevaiya?"

## How I built it

BenefitBot is constructed using the Strands Agents framework and deployed on Amazon Bedrock AgentCore Runtime. 

In traditional conversational agents, a massive LLM is asked to handle both the routing logic (deciding which tool to call) and the conversational response generation. This approach is sluggish, expensive, and frequently hallucinates tool parameters.

In BenefitBot, we separated decision-making from conversational generation:
- Strands Decider 2B: Specializes in one sharp task -- analyzing profile state and choosing the next tool action in under 2 seconds.
- Amazon Bedrock (Nova Pro/Lite): Takes the narrowed tool outputs and crafts warm, culturally sensitive, multilingual responses.
- AgentCore Runtime: Provides the serverless execution environment with native semantic and user preference memory strategies.

< FIGURE 1 of 5: upload submission/article/img/architecture.png here >
Alt text: Architecture: the user, the agent with its tools and decision, Amazon Bedrock and Strands Decider 2B

## The decision I handed to Strands Decider 2B

We handed the central tool routing decision to Strands Decider 2B (#tool-selection). In welfare discovery, searching without knowing the citizen's state leads to completely irrelevant schemes (for example, showing Maharashtra irrigation subsidies to a farmer in Kerala).

Strands Decider 2B evaluates the conversation profile using typed options:

```python
QUESTIONS = {
    "tool": Decider.choice(
        "Given the user profile, which tool should the agent call next?",
        {
            "search_schemes": (
                "the user's state IS known - search central and state government schemes now"
            ),
            "ask_more_questions": (
                "the user's state is unknown OR key profile fields are missing - "
                "ask the user one clarifying question before searching"
            ),
            "none": "no tool needed; the agent can answer directly",
        },
    )
}
```

When confidence is high (>= 0.7), the agent executes the selected tool immediately without second-guessing. When confidence falls below the threshold, the agent safely falls back to standard LLM arbitration, ensuring no citizen is locked out by an edge case.

## Measured

We benchmarked Strands Decider 2B against a general-purpose instruction LLM baseline across 14 labelled evaluation test cases representing diverse rural citizen scenarios.

Decider: strands-decider-2b (ugmdu). 14 labelled cases, 14 decisions.

| Metric | Strands Decider 2B | General LLM Baseline |
|---|---|---|
| Accuracy | 92.9% | 100.0% |
| Latency p50 per decision | 1878 ms | 11200 ms |
| Latency p95 | 1995 ms | 11500 ms |
| Cost per 1,000 decisions | $0.0350 | $0.1500 |
| Accuracy when confident (>= 0.7) | 100.0% | 100.0% |

At the median, Strands Decider 2B was 6.0x faster than the LLM (1.8 seconds vs 11.2 seconds) while delivering 100% accuracy when confident. For rural users connecting via erratic 3G or 4G mobile networks, shaving 9.3 seconds off every conversational turn is the difference between a usable public service and an abandoned session.

< FIGURE 2 of 5: upload submission/article/img/bench-accuracy.png here >
Alt text: Accuracy of Strands Decider 2B and the Bedrock LLM on the labelled cases

< FIGURE 3 of 5: upload submission/article/img/bench-latency.png here >
Alt text: Median latency per decision for both

< FIGURE 4 of 5: upload submission/article/img/bench-cost.png here >
Alt text: Cost per 1,000 decisions for both

< FIGURE 5 of 5: upload submission/article/img/bench-confidence.png here >
Alt text: Accuracy against the share of decisions answered without a human, as the confidence threshold moves

## The reusable decision pattern

The reusable pattern lives in `agent/decision.py` under `#tool-selection`. Any developer building public service, customer support, or multi-step workflow agents can drop this pattern into their codebase:

```python
from agent.decision import selector_for
selector = selector_for(decider)
narrowed_tools = selector.tools_for(user_message, history=conversation_history)
agent = Agent(model=bedrock_model, tools=narrowed_tools)
```

By decoupling tool pruning from conversational synthesis, your agent runs faster, costs a fraction of standard LLM-only pipelines, and guarantees deterministic boundaries on critical workflows.

## What I learned and what is next

Building BenefitBot reinforced a fundamental insight: AI in the public sector should not be about flashy parlor tricks; it must solve real structural exclusion. With 1.4 billion people and thousands of government schemes, the challenge has never been lack of welfare -- it has been lack of navigation.

By combining the lightweight speed of Strands Decider 2B with the conversational fluency of Amazon Bedrock and the managed durability of AgentCore Runtime, we can give every citizen a knowledgeable, multilingual welfare guide in their pocket.

Next steps for BenefitBot:
1. Integration with voice-based IVR and WhatsApp Business API to reach citizens without smartphones.
2. Expanding the scheme knowledge base across all 28 states and 8 union territories.
3. Automated integration with DigiLocker to verify document eligibility with explicit citizen consent.

---

Tags: #strands-decider-2b #tool-selection

Built with the AWS Student Builder Group VVCE Strands Decider hackathon kit
