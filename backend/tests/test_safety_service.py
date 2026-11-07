from app.services.safety_service import (
    EMERGENCY_NOTICE,
    SELF_HARM_NOTICE,
    add_safety_notices,
)


def test_no_notice_for_normal_question():
    answer = add_safety_notices(
        "What does hemoglobin measure?",
        "Hemoglobin carries oxygen in the blood.",
    )

    assert EMERGENCY_NOTICE not in answer
    assert SELF_HARM_NOTICE not in answer


def test_emergency_notice_when_question_mentions_red_flag():
    answer = add_safety_notices(
        "I have chest pain, what does my report say?",
        "Your report lists a normal ECG.",
    )

    assert answer.endswith(EMERGENCY_NOTICE)


def test_emergency_notice_when_only_answer_mentions_red_flag():
    answer = add_safety_notices(
        "What is costochondritis?",
        "It causes chest pain near the breastbone.",
    )

    assert answer.endswith(EMERGENCY_NOTICE)


def test_matching_ignores_case():
    answer = add_safety_notices(
        "SHORTNESS OF BREATH after walking?",
        "Please see a doctor.",
    )

    assert EMERGENCY_NOTICE in answer


def test_self_harm_notice_goes_first():
    answer = add_safety_notices(
        "I want to kill myself",
        "I'm sorry you're feeling this way.",
    )

    assert answer.startswith(SELF_HARM_NOTICE)


def test_self_harm_not_triggered_by_answer_text():
    answer = add_safety_notices(
        "What is iron toxicity?",
        "Iron overdose and self-harm cases are seen in hospitals.",
    )

    assert SELF_HARM_NOTICE not in answer


def test_word_boundary_avoids_false_match():
    answer = add_safety_notices(
        "Is my blood pressure fine?",
        "Brushstrokes of good habits help.",
    )

    assert EMERGENCY_NOTICE not in answer