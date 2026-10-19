"""BenefitBot tools: scheme search, eligibility check, document checklist.

Each tool has a clear one-line docstring — the tool-selection pattern reads it as the
option description when Strands Decider 2B picks which tool to call.

Decision design (2 options the decider chooses between):
  search_schemes       — user's state IS known; find matching schemes
  ask_more_questions   — user's state OR key profile fields are MISSING; ask first
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from strands import tool

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

_DATA = Path(__file__).parent / "data"


def _load(filename: str) -> list[dict]:
    path = _DATA / filename
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _all_schemes() -> list[dict]:
    return _load("central_schemes.json") + _load("state_schemes.json")


# ---------------------------------------------------------------------------
# Profile helpers
# ---------------------------------------------------------------------------

CATEGORIES = ["farmer", "woman", "student", "senior", "disabled", "general"]
SUPPORTED_LANGUAGES = {
    "english": "English",
    "hindi": "Hindi",
    "tamil": "Tamil",
    "telugu": "Telugu",
    "bengali": "Bengali",
    "marathi": "Marathi",
    "kannada": "Kannada",
}

# Canonical state names + common aliases (lowercase key → canonical value)
_STATE_ALIASES: dict[str, str] = {
    # exact lowercase canonical names
    "andhra pradesh": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "orissa": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu",
    "tamilnadu": "Tamil Nadu",
    "tn": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh",
    "up": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "uttaranchal": "Uttarakhand",
    "west bengal": "West Bengal",
    "wb": "West Bengal",
    "bengal": "West Bengal",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "jammu and kashmir": "Jammu and Kashmir",
    "j&k": "Jammu and Kashmir",
    "jk": "Jammu and Kashmir",
    "ladakh": "Ladakh",
    "ap": "Andhra Pradesh",
    "mp": "Madhya Pradesh",
    "hp": "Himachal Pradesh",
    "ka": "Karnataka",
    "mh": "Maharashtra",
    "kl": "Kerala",
    "ga": "Goa",
    "br": "Bihar",
    "rj": "Rajasthan",
    "hr": "Haryana",
    "pb": "Punjab",
    "as": "Assam",
    "jh": "Jharkhand",
    "cg": "Chhattisgarh",
    "uk": "Uttarakhand",
    "mn": "Manipur",
    "ml": "Meghalaya",
    "mz": "Mizoram",
    "nl": "Nagaland",
    "sk": "Sikkim",
    "tr": "Tripura",
    "ar": "Arunachal Pradesh",
    "od": "Odisha",
    "ts": "Telangana",
    "tg": "Telangana",
}

INDIAN_STATES = sorted(set(_STATE_ALIASES.values()))


def normalise_state(raw: str) -> str:
    """Map any common state spelling/abbreviation to the canonical title-case name."""
    key = raw.strip().lower()
    if key in _STATE_ALIASES:
        return _STATE_ALIASES[key]
    # Try title-case direct match
    titled = raw.strip().title()
    if titled in set(_STATE_ALIASES.values()):
        return titled
    # Partial match: if the input is a substring of exactly one canonical name
    matches = [v for k, v in _STATE_ALIASES.items() if key in k or k in k]
    canonical_matches = list({v for k, v in _STATE_ALIASES.items() if key in k})
    if len(canonical_matches) == 1:
        return canonical_matches[0]
    return titled  # return as-is (title-cased) if no match; LLM will handle it


def normalise_income_lpa(raw: float) -> float:
    """Convert income to LPA regardless of what unit the user gave.

    Heuristic:
    - value < 25        → already in LPA (e.g. 1.5 means Rs 1.5 lakh/year)
    - 25 <= value < 500 → monthly income in thousands (e.g. 10 means Rs 10,000/month → 1.2 LPA)
    - 500 <= value      → annual income in rupees (e.g. 150000 → 1.5 LPA)
                          or monthly rupees (e.g. 5000/month → 0.06 LPA)
    We treat values >= 10000 as annual rupees, 500-9999 as monthly rupees.
    """
    if raw <= 0:
        return 0.0
    if raw < 25:
        return round(raw, 2)          # already LPA
    if raw < 500:
        # treat as monthly income in thousands (e.g. user typed "10" meaning 10k/month)
        return round(raw * 12 / 100, 2)   # 10 * 12 / 100 = 1.2 LPA
    if raw < 10000:
        # monthly rupees (e.g. 5000 /month)
        return round(raw * 12 / 100000, 2)
    # annual rupees (e.g. 150000)
    return round(raw / 100000, 2)


def _match_scheme(scheme: dict, profile: dict) -> bool:
    """Return True if scheme is potentially relevant given the profile."""
    cat = profile.get("category", "general")
    age = profile.get("age")
    income_lpa = profile.get("income_lpa")
    state = profile.get("state", "").strip().lower()

    # Category match
    scheme_cats = scheme.get("category", ["general"])
    if cat != "general" and "general" not in scheme_cats and cat not in scheme_cats:
        return False

    # Age match
    if age is not None:
        if scheme.get("min_age") and age < scheme["min_age"]:
            return False
        if scheme.get("max_age") and age > scheme["max_age"]:
            return False

    # Income match
    if income_lpa is not None and scheme.get("max_income_lpa") is not None:
        if income_lpa > scheme["max_income_lpa"]:
            return False

    # State match (central schemes have state=null and always match)
    scheme_state = (scheme.get("state") or "").strip().lower()
    if scheme_state and state and scheme_state != state:
        return False

    return True


def _eligibility_note(scheme: dict, profile: dict) -> str:
    unknown = []
    if not profile.get("age"):
        unknown.append("age")
    if not profile.get("income_lpa") and scheme.get("max_income_lpa"):
        unknown.append("income")
    if not profile.get("state") and scheme.get("state"):
        unknown.append("state")
    if unknown:
        return f"POTENTIAL eligibility (confirm {', '.join(unknown)} to verify)"
    return "POTENTIAL eligibility based on your profile (official verification required at application)"


def _format_scheme(scheme: dict, profile: dict) -> dict[str, Any]:
    return {
        "name": scheme["name"],
        "full_name": scheme["full_name"],
        "level": scheme["level"],
        "state": scheme.get("state"),
        "benefit": scheme["benefit"],
        "eligibility_note": _eligibility_note(scheme, profile),
        "slug": scheme["slug"],
    }


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def get_user_profile(
    state: str = "",
    age: int = 0,
    occupation: str = "",
    income: float = 0.0,
    category: str = "",
    language: str = "english",
) -> dict:
    """Collect or update the user's profile: state, age, occupation, income, category, language.

    income accepts any unit (LPA, monthly rupees, annual rupees) and normalises automatically.
    """
    profile: dict[str, Any] = {}
    if state:
        profile["state"] = normalise_state(state)
    if age and age > 0:
        profile["age"] = int(age)
    if occupation:
        profile["occupation"] = occupation.strip().lower()
    if income and income > 0:
        profile["income_lpa"] = normalise_income_lpa(float(income))
        profile["income_display"] = f"Rs {profile['income_lpa']:.2f} lakh/year"
    cat = category.strip().lower()
    if cat in CATEGORIES:
        profile["category"] = cat
    elif cat:
        # map common variants
        _cat_map = {
            "student": "student", "farmer": "farmer", "women": "woman", "woman": "woman",
            "female": "woman", "girl": "woman", "senior citizen": "senior",
            "old": "senior", "elderly": "senior", "pension": "senior",
            "disabled": "disabled", "handicapped": "disabled", "divyang": "disabled",
        }
        profile["category"] = _cat_map.get(cat, "general")
    lang = language.strip().lower()
    profile["language"] = lang if lang in SUPPORTED_LANGUAGES else "english"
    profile["_status"] = "profile_updated"
    return profile


@tool
def search_schemes(
    state: str,
    age: int = 0,
    category: str = "general",
    income: float = 0.0,
) -> dict:
    """Search central and state government schemes when the user's state is known.

    income accepts any unit (LPA, monthly rupees, annual rupees).
    """
    canonical_state = normalise_state(state)
    income_lpa = normalise_income_lpa(float(income)) if income else None
    profile = {
        "state": canonical_state,
        "age": int(age) if age else None,
        "category": category.strip().lower() if category else "general",
        "income_lpa": income_lpa,
    }
    central = [s for s in _load("central_schemes.json") if _match_scheme(s, profile)]
    state_schemes = [s for s in _load("state_schemes.json") if _match_scheme(s, profile)]
    state_in_data = {s.get("state", "").strip().title() for s in _load("state_schemes.json")}
    note = (
        f"Showing central (nationwide) and state schemes for {canonical_state}."
        if canonical_state in state_in_data
        else (
            f"Showing central (nationwide) schemes. "
            f"No state-specific data found for {canonical_state}; "
            f"central schemes apply to all states."
        )
    )
    return {
        "source": "both",
        "state": canonical_state,
        "central_count": len(central),
        "state_count": len(state_schemes),
        "central_schemes": [_format_scheme(s, profile) for s in central],
        "state_schemes": [_format_scheme(s, profile) for s in state_schemes],
        "note": note,
    }


@tool
def ask_more_questions(missing_fields: str = "state,category") -> dict:
    """Ask the user for missing profile information (state, age, income, category) before searching schemes."""
    fields = [f.strip() for f in missing_fields.split(",") if f.strip()]
    if not fields:
        fields = ["state", "category"]
    questions_map = {
        "state": "Which state in India do you live in?",
        "age": "How old are you?",
        "category": f"Which best describes you? Options: {', '.join(CATEGORIES)}",
        "income": "What is your approximate monthly or annual income? (e.g. Rs 5,000/month or Rs 1.5 lakh/year)",
        "income_lpa": "What is your approximate annual income in lakhs? (e.g. 1.5 for Rs 1.5 lakh/year)",
        "occupation": "What is your occupation? (e.g. farmer, daily wage worker, homemaker, student)",
    }
    questions = [questions_map.get(f, f"Please tell me your {f}.") for f in fields]
    return {
        "_action": "ask_user",
        "missing": fields,
        "questions": questions,
        "note": "Please answer so I can find the right schemes for you.",
    }


@tool
def get_document_checklist(scheme_slug: str, language: str = "english") -> dict:
    """Return the required documents and application steps for a specific scheme by its slug."""
    schemes = _all_schemes()
    scheme = next((s for s in schemes if s["slug"] == scheme_slug), None)
    if not scheme:
        # Try partial slug match
        scheme = next((s for s in schemes if scheme_slug.lower() in s["slug"]), None)
    if not scheme:
        available = [s["slug"] for s in schemes[:10]]
        return {
            "error": f"Scheme '{scheme_slug}' not found.",
            "hint": f"Try one of these slugs: {available}",
        }
    lang = language.strip().lower()
    lang_label = SUPPORTED_LANGUAGES.get(lang, "English")
    return {
        "scheme_name": scheme["name"],
        "full_name": scheme["full_name"],
        "benefit": scheme["benefit"],
        "documents_required": scheme.get("documents", []),
        "application_steps": scheme.get("application_steps", []),
        "apply_url": scheme.get("apply_url", ""),
        "language": lang_label,
        "note": (
            f"Eligibility is POTENTIAL based on your profile; "
            "official verification is required at the application stage."
        ),
    }


TOOLS = [
    get_user_profile,
    search_schemes,
    ask_more_questions,
    get_document_checklist,
]
