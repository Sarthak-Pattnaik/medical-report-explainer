import re


# Signs that can mean a medical emergency. Checked in both the
# user's question and the AI's answer.
EMERGENCY_PATTERNS = [
    r"chest pain",
    r"chest (tightness|pressure)",
    r"short(ness)? of breath",
    r"(difficulty|trouble) breathing",
    r"can'?t breathe",
    r"cannot breathe",
    r"\bfaint(ed|ing)?\b",
    r"passed out",
    r"unconscious",
    r"seizure",
    r"\bstroke\b",
    r"slurred speech",
    r"face droop",
    r"sudden (weakness|numbness)",
    r"heart attack",
    r"vomiting blood",
    r"coughing (up )?blood",
    r"severe bleeding",
    r"anaphylaxis",
    r"severe allergic",
]

# Signs of possible self-harm. Checked only in the user's message,
# so medical explanations that mention "overdose" don't trigger it.
SELF_HARM_PATTERNS = [
    r"suicid",
    r"kill myself",
    r"end my life",
    r"self[- ]?harm",
    r"hurt myself",
]

EMERGENCY_NOTICE = (
    "**If you or someone else has chest pain, trouble breathing, "
    "fainting, sudden weakness, or other severe symptoms, seek "
    "emergency medical care now. In India, call 112.**"
)

SELF_HARM_NOTICE = (
    "**If you are thinking about harming yourself, you don't have "
    "to face this alone. In India, call Tele-MANAS on 14416 "
    "(free, 24/7), or 112 in an emergency.**"
)


def _matches_any(patterns: list[str], text: str) -> bool:
    return any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in patterns
    )


def add_safety_notices(user_message: str, answer: str) -> str:
    """
    Add fixed safety notices to a chat answer when the
    conversation touches on emergencies or self-harm.
    """

    if _matches_any(SELF_HARM_PATTERNS, user_message):
        answer = f"{SELF_HARM_NOTICE}\n\n{answer}"

    if _matches_any(EMERGENCY_PATTERNS, f"{user_message}\n{answer}"):
        answer = f"{answer}\n\n{EMERGENCY_NOTICE}"

    return answer