from datetime import datetime, timezone

from app.services.report_history_service import format_timestamp


# 20:15 UTC on Nov 5 is 01:45 on Nov 6 in India.
UPLOADED_AT = datetime(2026, 11, 5, 20, 15, tzinfo=timezone.utc)


def test_formats_in_user_timezone():
    assert format_timestamp(UPLOADED_AT, "Asia/Kolkata") == (
        "2026-11-06 01:45 IST"
    )


def test_falls_back_to_utc_without_timezone():
    assert format_timestamp(UPLOADED_AT, None) == "2026-11-05 20:15 UTC"


def test_falls_back_to_utc_for_unknown_timezone():
    assert format_timestamp(UPLOADED_AT, "Not/A_Zone") == (
        "2026-11-05 20:15 UTC"
    )


def test_rejects_path_like_timezone_safely():
    assert format_timestamp(UPLOADED_AT, "../../etc/passwd") == (
        "2026-11-05 20:15 UTC"
    )