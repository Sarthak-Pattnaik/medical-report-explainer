"""
Helpers that keep AI prompts within Groq's token limit.

On the free tier, one request may use at most 8,000 tokens per
minute, and Groq counts the prompt plus the tokens reserved for
the answer. A long report with many results goes over this limit,
so these helpers shorten what is sent.
"""

from app.services.text_chunking import CHARS_PER_TOKEN, estimate_tokens

# Groq free-tier limit for one request (prompt + answer).
TOKEN_LIMIT = 8000

# Extra room, because estimate_tokens is only approximate.
SAFETY_MARGIN = 500

# Fields the AI needs to talk about a result.
PARAMETER_FIELDS = ("name", "value", "unit", "flag", "reference_range")

# Short enough to keep the prompt small, long enough to show
# the line the value came from. Source lines are full of line
# breaks and units, which cost more tokens than plain words.
SOURCE_TEXT_CHARS = 100

# Clinical context items sent per category.
MAX_CONTEXT_ITEMS = 8

# Flagged results named in the fallback observation.
MAX_FLAGGED_NAMES = 10

OMITTED_MARKER = "\n[... part of the report left out to fit the AI limit ...]\n"


def tokens_left(max_completion_tokens: int, *parts: str) -> int:
    """
    Tokens still free for one request after the answer and the
    given prompt parts. Never below zero.
    """

    used = sum(estimate_tokens(part) for part in parts)
    left = TOKEN_LIMIT - SAFETY_MARGIN - max_completion_tokens - used

    return max(left, 0)


def flag_priority(flag) -> int:
    """
    0 for critical results, 1 for high or low results,
    2 for everything else. Lower comes first.
    """

    text = str(flag or "").strip().lower()

    if "critical" in text or "panic" in text:
        return 0

    if text in {"high", "low", "h", "l", "abnormal", "a"}:
        return 1

    return 2


def select_parameters(parameters: list[dict], limit: int) -> list[dict]:
    """
    Pick up to `limit` results: critical first, then high or low,
    then the rest. The picked results keep their report order.
    """

    ranked = sorted(
        range(len(parameters)),
        key=lambda index: (
            flag_priority(parameters[index].get("flag")),
            index,
        ),
    )

    picked = sorted(ranked[:limit])

    return [parameters[index] for index in picked]


def flagged_observations(parameters: list[dict]) -> list[str]:
    """
    A plain observation built from the report's own flags, used
    when the AI returns no observations. Empty if nothing is
    flagged.
    """

    flagged = [
        f"{parameter.get('name')} ({parameter.get('flag')})"
        for parameter in parameters
        if flag_priority(parameter.get("flag")) < 2
    ]

    if not flagged:
        return []

    names = ", ".join(flagged[:MAX_FLAGGED_NAMES])
    more = len(flagged) - MAX_FLAGGED_NAMES

    if more > 0:
        names += f" and {more} more"

    return [
        f"The report flags {len(flagged)} result(s) outside the "
        f"reference range: {names}. Please discuss these with "
        "your doctor."
    ]


def compact_parameter(parameter: dict) -> dict:
    """
    Keep the fields the AI needs and a short source line.
    """

    compact = {field: parameter.get(field) for field in PARAMETER_FIELDS}

    source_text = parameter.get("source_text")

    if source_text:
        compact["source_text"] = str(source_text)[:SOURCE_TEXT_CHARS]

    return compact


def parameter_line(parameter: dict) -> str:
    """
    One result as a short line, for example:
    "Haemoglobin: 11.8 g/dL | range: 13.0 - 17.0 | flag: low"
    """

    value = parameter.get("value")
    unit = parameter.get("unit")

    result = "not given" if value is None else str(value)

    if unit:
        result = f"{result} {unit}"

    parts = [f"{parameter.get('name')}: {result}"]

    if parameter.get("reference_range"):
        parts.append(f"range: {parameter['reference_range']}")

    if parameter.get("flag"):
        parts.append(f"flag: {parameter['flag']}")

    return " | ".join(parts)


def compact_clinical_context(clinical_context: dict | None) -> dict:
    """
    Drop confidence values and shorten source lines.
    """

    compact = {}

    for category, items in (clinical_context or {}).items():
        if not isinstance(items, list):
            continue

        compact[category] = [
            (
                {
                    "text": item.get("text"),
                    "source_text": (
                        str(item["source_text"])[:SOURCE_TEXT_CHARS]
                        if item.get("source_text")
                        else None
                    ),
                }
                if isinstance(item, dict)
                else item
            )
            for item in items[:MAX_CONTEXT_ITEMS]
        ]

    return compact


def shorten_text(text: str, max_chars: int) -> str:
    """
    Keep the start and the end of a long text. Patient details
    are usually at the start, and conclusions at the end.
    """

    if len(text) <= max_chars:
        return text

    if max_chars <= len(OMITTED_MARKER):
        return text[:max(max_chars, 0)]

    room = max_chars - len(OMITTED_MARKER)
    head = room * 2 // 3
    tail = room - head

    return text[:head] + OMITTED_MARKER + (text[-tail:] if tail else "")


def chars_for_tokens(tokens: int) -> int:
    return tokens * CHARS_PER_TOKEN
