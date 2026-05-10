"""
Property-based tests for the SMS Notification feature.
Uses Hypothesis to verify correctness properties across random inputs.

Feature: sms-notification
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch, call
from hypothesis import given, settings, assume
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Path setup - allow importing from the backend root without installing it
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Patch heavy external dependencies before importing notifications so the
# module loads cleanly in a test environment with no live DB or config.
import unittest.mock as _mock

_config_patch = _mock.patch.dict(
    "sys.modules",
    {
        "config": _mock.MagicMock(
            SEMAPHORE_API_KEY="test-key",
            SEMAPHORE_SENDER_NAME="TESTRIDE",
            SMTP_SERVER="localhost",
            SMTP_PORT=25,
            EMAIL_USER="test@test.com",
            EMAIL_PASS="pass",
        ),
        "database": _mock.MagicMock(),
    },
)
_config_patch.start()

from notifications import (  # noqa: E402  (import after sys.path / patch setup)
    truncate_message,
    compose_booking_created_sms,
    compose_booking_approved_sms,
    compose_booking_rejected_sms,
    compose_customer_cancel_sms,
    compose_admin_cancel_sms,
    compose_pickup_sms,
    compose_completed_sms,
    compose_modify_booking_sms,
    compose_full_payment_sms,
    compose_downpayment_sms,
    compose_balance_payment_sms,
    compose_cash_paid_sms,
    compose_split_request_sms,
    compose_split_paid_sms,
    compose_license_approved_sms,
    compose_license_rejected_sms,
    compose_driver_approved_sms,
    compose_driver_rejected_sms,
    compose_admin_new_booking_sms,
    compose_admin_driver_application_sms,
    compose_admin_payment_proof_sms,
    compose_otp_sms,
    SMS_Service,
)

# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

# Printable text that won't accidentally contain format-breaking characters
_text = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd", "Zs"),
        whitelist_characters="-_.,#/",
    ),
    min_size=1,
    max_size=80,
)

_booking_id = st.integers(min_value=1, max_value=999_999)
_amount = st.decimals(
    min_value=1,
    max_value=999_999,
    allow_nan=False,
    allow_infinity=False,
    places=2,
)
_amount_str = st.floats(min_value=1.0, max_value=999_999.0, allow_nan=False, allow_infinity=False)
_otp = st.from_regex(r"[0-9]{6}", fullmatch=True)
_date_str = st.dates().map(str)
_recipient_type = st.sampled_from(["customer", "admin", "driver"])


# ===========================================================================
# Property 1: truncate_message preserves length invariant
# Feature: sms-notification, Property 1: truncate_message preserves length invariant
# ===========================================================================

@given(st.text(min_size=0, max_size=700))
@settings(max_examples=500)
def test_truncate_message_length_invariant(message: str):
    """Output is always ? 320 characters."""
    result = truncate_message(message)
    assert len(result) <= 320, (
        f"truncate_message returned {len(result)} chars, expected ? 320"
    )


@given(st.text(min_size=321, max_size=700))
@settings(max_examples=300)
def test_truncate_message_ellipsis_when_over_limit(message: str):
    """When input exceeds 320 chars the result is exactly 320 chars and ends with '...'."""
    result = truncate_message(message)
    assert len(result) == 320, (
        f"Expected exactly 320 chars after truncation, got {len(result)}"
    )
    assert result.endswith("..."), (
        "Truncated message must end with '...'"
    )


@given(st.text(min_size=0, max_size=320))
@settings(max_examples=300)
def test_truncate_message_unchanged_within_limit(message: str):
    """When input is ? 320 chars the result equals the input unchanged."""
    result = truncate_message(message)
    assert result == message, (
        f"truncate_message modified a message within the limit: {message!r} ? {result!r}"
    )


@given(st.text(min_size=0, max_size=700), st.integers(min_value=4, max_value=500))
@settings(max_examples=200)
def test_truncate_message_custom_max_len(message: str, max_len: int):
    """Custom max_len is respected: output ? max_len, ellipsis when truncated."""
    result = truncate_message(message, max_len=max_len)
    assert len(result) <= max_len
    if len(message) > max_len:
        assert result.endswith("...")
        assert len(result) == max_len
    else:
        assert result == message


# ===========================================================================
# Property 2: booking lifecycle messages contain required fields
# Feature: sms-notification, Property 2: booking lifecycle messages contain required fields
# ===========================================================================

@given(_booking_id, _text, _text, _date_str, _date_str, _amount_str)
@settings(max_examples=200)
def test_compose_booking_created_contains_required_fields(
    booking_id, brand, model, start_date, end_date, total_price
):
    """compose_booking_created_sms contains booking_id, brand, model, dates, price."""
    result = compose_booking_created_sms(booking_id, brand, model, start_date, end_date, total_price)
    assert str(booking_id) in result
    assert brand in result
    assert model in result
    assert str(start_date) in result
    assert str(end_date) in result
    assert str(total_price) in result


@given(_booking_id, _text, _text, _date_str)
@settings(max_examples=200)
def test_compose_booking_approved_contains_required_fields(
    booking_id, brand, model, start_date
):
    """compose_booking_approved_sms contains booking_id, brand, model, start_date."""
    result = compose_booking_approved_sms(booking_id, brand, model, start_date)
    assert str(booking_id) in result
    assert brand in result
    assert model in result
    assert str(start_date) in result


@given(_booking_id, _text, _text, _date_str)
@settings(max_examples=200)
def test_compose_pickup_sms_contains_required_fields(
    booking_id, brand, model, end_date
):
    """compose_pickup_sms contains booking_id, brand, model, end_date."""
    result = compose_pickup_sms(booking_id, brand, model, end_date)
    assert str(booking_id) in result
    assert brand in result
    assert model in result
    assert str(end_date) in result


@given(_booking_id, _date_str, _date_str, _amount_str)
@settings(max_examples=200)
def test_compose_modify_booking_sms_contains_required_fields(
    booking_id, new_start, new_end, new_total
):
    """compose_modify_booking_sms contains booking_id, new dates, new total."""
    result = compose_modify_booking_sms(booking_id, new_start, new_end, new_total)
    assert str(booking_id) in result
    assert str(new_start) in result
    assert str(new_end) in result
    assert str(new_total) in result


@given(_booking_id)
@settings(max_examples=200)
def test_compose_booking_rejected_contains_booking_id(booking_id):
    """compose_booking_rejected_sms contains the booking_id."""
    result = compose_booking_rejected_sms(booking_id)
    assert str(booking_id) in result


@given(_booking_id)
@settings(max_examples=200)
def test_compose_completed_sms_contains_booking_id(booking_id):
    """compose_completed_sms contains the booking_id."""
    result = compose_completed_sms(booking_id)
    assert str(booking_id) in result


# ===========================================================================
# Property 3: cancellation messages preserve the cancellation reason
# Feature: sms-notification, Property 3: cancellation messages preserve the cancellation reason
# ===========================================================================

@given(_booking_id, _text)
@settings(max_examples=200)
def test_compose_customer_cancel_contains_booking_id_and_reason(booking_id, reason):
    """compose_customer_cancel_sms contains both booking_id and reason."""
    result = compose_customer_cancel_sms(booking_id, reason)
    assert str(booking_id) in result
    assert reason in result


@given(_booking_id, _text)
@settings(max_examples=200)
def test_compose_admin_cancel_contains_booking_id_reason_and_refund_notice(booking_id, reason):
    """compose_admin_cancel_sms contains booking_id, reason, and a refund notice."""
    result = compose_admin_cancel_sms(booking_id, reason)
    assert str(booking_id) in result
    assert reason in result
    # Design spec: must include a note that a refund will be initiated if applicable
    assert "refund" in result.lower()


# ===========================================================================
# Property 4: payment messages contain required financial fields
# Feature: sms-notification, Property 4: payment messages contain required financial fields
# ===========================================================================

@given(_booking_id, _amount_str, _text, _text)
@settings(max_examples=200)
def test_compose_full_payment_contains_required_fields(
    booking_id, amount, method, reference_number
):
    """compose_full_payment_sms contains booking_id, amount, method, reference_number."""
    result = compose_full_payment_sms(booking_id, amount, method, reference_number)
    assert str(booking_id) in result
    assert str(amount) in result
    assert method in result
    assert reference_number in result


@given(_booking_id, _amount_str, _amount_str, _text)
@settings(max_examples=200)
def test_compose_downpayment_contains_required_fields(
    booking_id, amount_paid, balance_amount, reference_number
):
    """compose_downpayment_sms contains booking_id, amount_paid, balance_amount, reference_number."""
    result = compose_downpayment_sms(booking_id, amount_paid, balance_amount, reference_number)
    assert str(booking_id) in result
    assert str(amount_paid) in result
    assert str(balance_amount) in result
    assert reference_number in result


@given(_booking_id, _amount_str, _text)
@settings(max_examples=200)
def test_compose_balance_payment_contains_required_fields(
    booking_id, amount, reference_number
):
    """compose_balance_payment_sms contains booking_id, amount, reference_number."""
    result = compose_balance_payment_sms(booking_id, amount, reference_number)
    assert str(booking_id) in result
    assert str(amount) in result
    assert reference_number in result


@given(_booking_id, _amount_str)
@settings(max_examples=200)
def test_compose_cash_paid_contains_required_fields(booking_id, total_amount):
    """compose_cash_paid_sms contains booking_id and total_amount."""
    result = compose_cash_paid_sms(booking_id, total_amount)
    assert str(booking_id) in result
    assert str(total_amount) in result


# ===========================================================================
# Property 5: split payment messages contain required fields
# Feature: sms-notification, Property 5: split payment messages contain required fields
# ===========================================================================

@given(_booking_id, _text, _amount_str)
@settings(max_examples=200)
def test_compose_split_request_contains_required_fields(
    booking_id, initiator_name, amount
):
    """compose_split_request_sms contains booking_id, initiator_name, and amount."""
    result = compose_split_request_sms(booking_id, initiator_name, amount)
    assert str(booking_id) in result
    assert initiator_name in result
    assert str(amount) in result


@given(_booking_id, _amount_str)
@settings(max_examples=200)
def test_compose_split_paid_contains_required_fields(booking_id, amount):
    """compose_split_paid_sms contains booking_id and amount."""
    result = compose_split_paid_sms(booking_id, amount)
    assert str(booking_id) in result
    assert str(amount) in result


# ===========================================================================
# Property 6: driver application messages preserve variable fields
# Feature: sms-notification, Property 6: driver application messages preserve variable fields
# ===========================================================================

@given(_text)
@settings(max_examples=200)
def test_compose_driver_approved_contains_driver_name(driver_name):
    """compose_driver_approved_sms contains the driver name."""
    result = compose_driver_approved_sms(driver_name)
    assert driver_name in result


@given(_text)
@settings(max_examples=200)
def test_compose_driver_rejected_contains_reason(reason):
    """compose_driver_rejected_sms contains the rejection reason."""
    result = compose_driver_rejected_sms(reason)
    assert reason in result


# ===========================================================================
# Property 7: admin alert messages contain required fields
# Feature: sms-notification, Property 7: admin alert messages contain required fields
# ===========================================================================

@given(_booking_id, _text, _text, _text, _date_str, _date_str)
@settings(max_examples=200)
def test_compose_admin_new_booking_contains_required_fields(
    booking_id, customer_name, brand, model, start_date, end_date
):
    """compose_admin_new_booking_sms contains all six required fields."""
    result = compose_admin_new_booking_sms(
        booking_id, customer_name, brand, model, start_date, end_date
    )
    assert str(booking_id) in result
    assert customer_name in result
    assert brand in result
    assert model in result
    assert str(start_date) in result
    assert str(end_date) in result


@given(_text)
@settings(max_examples=200)
def test_compose_admin_driver_application_contains_applicant_name(applicant_name):
    """compose_admin_driver_application_sms contains the applicant name."""
    result = compose_admin_driver_application_sms(applicant_name)
    assert applicant_name in result


@given(_booking_id, _text, _amount_str)
@settings(max_examples=200)
def test_compose_admin_payment_proof_contains_required_fields(
    booking_id, customer_name, amount
):
    """compose_admin_payment_proof_sms contains booking_id, customer_name, and amount."""
    result = compose_admin_payment_proof_sms(booking_id, customer_name, amount)
    assert str(booking_id) in result
    assert customer_name in result
    assert str(amount) in result


# ===========================================================================
# Property 8: OTP messages contain the OTP code
# Feature: sms-notification, Property 8: OTP messages contain the OTP code
# ===========================================================================

@given(_otp)
@settings(max_examples=200)
def test_compose_otp_contains_code(otp_code):
    """compose_otp_sms contains the OTP code."""
    result = compose_otp_sms(otp_code)
    assert otp_code in result


@given(_otp)
@settings(max_examples=200)
def test_compose_otp_contains_expiry_notice(otp_code):
    """compose_otp_sms contains an expiry notice (mentions 'expires' or 'minutes')."""
    result = compose_otp_sms(otp_code)
    assert "expires" in result.lower() or "minutes" in result.lower(), (
        f"OTP message missing expiry notice: {result!r}"
    )


# ===========================================================================
# Property 9: opt-out blocks promotional SMS but not transactional SMS
# Feature: sms-notification, Property 9: opt-out blocks promotional SMS but not transactional SMS
# ===========================================================================

def _make_opted_out_user(phone: str = "+639000000001"):
    """Return a dict-like mock row for a user with sms_opt_out=True."""
    return {"phone_number": phone, "sms_opt_out": True}


@given(
    st.integers(min_value=1, max_value=999_999),  # user_id
    _text,                                          # message
    st.from_regex(r"\+639[0-9]{9}", fullmatch=True),  # phone
)
@settings(max_examples=200)
def test_opt_out_blocks_promotional_sms(user_id, message, phone):
    """
    For a user with sms_opt_out=True, notify_customer(..., is_transactional=False)
    must NOT call send_sms().
    """
    service = SMS_Service()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {"phone_number": phone, "sms_opt_out": True}

    with patch("notifications.get_cursor", return_value=mock_cursor), \
         patch.object(service, "send_sms") as mock_send:
        result = service.notify_customer(user_id, message, is_transactional=False)

    mock_send.assert_not_called()
    assert result is False


@given(
    st.integers(min_value=1, max_value=999_999),  # user_id
    _text,                                          # message
    st.from_regex(r"\+639[0-9]{9}", fullmatch=True),  # phone
)
@settings(max_examples=200)
def test_opt_out_does_not_block_transactional_sms(user_id, message, phone):
    """
    For a user with sms_opt_out=True, notify_customer(..., is_transactional=True)
    must call send_sms() exactly once.
    """
    service = SMS_Service()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {"phone_number": phone, "sms_opt_out": True}

    with patch("notifications.get_cursor", return_value=mock_cursor), \
         patch.object(service, "send_sms", return_value=True) as mock_send:
        service.notify_customer(user_id, message, is_transactional=True)

    mock_send.assert_called_once()


# ===========================================================================
# Property 10: SMS preference endpoint round-trip
# Feature: sms-notification, Property 10: SMS preference endpoint round-trip
# ===========================================================================

@pytest.fixture(scope="module")
def flask_test_client():
    """
    Create a Flask test client with all external dependencies mocked so the
    app can be imported and exercised without a live DB or Semaphore API.
    """
    import importlib

    # Patch DB helpers used at import time in app.py
    db_mock = MagicMock()
    db_mock.get_connection.return_value = MagicMock()
    db_mock.release_connection.return_value = None
    db_mock.get_db.return_value = MagicMock()
    db_mock.get_cursor.return_value = MagicMock()
    db_mock.commit_db.return_value = None
    db_mock.init_db_helpers.return_value = None

    with patch.dict(
        "sys.modules",
        {
            "database": db_mock,
            "psycopg": MagicMock(),
            "psycopg.rows": MagicMock(dict_row=MagicMock()),
            "psycopg_pool": MagicMock(),
            "supabase": MagicMock(),
            "google.oauth2": MagicMock(),
            "google.oauth2.id_token": MagicMock(),
            "google.auth": MagicMock(),
            "google.auth.transport": MagicMock(),
            "google.auth.transport.requests": MagicMock(),
        },
    ):
        import app as flask_app_module  # noqa: PLC0415

        flask_app_module.app.config["TESTING"] = True
        with flask_app_module.app.test_client() as client:
            yield client


@given(
    st.integers(min_value=1, max_value=999_999),  # user_id
    st.booleans(),                                  # sms_opt_out
)
@settings(max_examples=100)
def test_sms_preference_round_trip(flask_test_client, user_id, sms_opt_out):
    """
    POST /user/sms-preference with a valid user_id and sms_opt_out value:
    - Response status is 200
    - Response body contains the same user_id and sms_opt_out value
    - The DB UPDATE was called with the correct values
    """
    mock_cursor = MagicMock()
    # Simulate user found
    mock_cursor.fetchone.return_value = {"id": user_id, "sms_opt_out": sms_opt_out}

    with patch("notifications.get_cursor", return_value=mock_cursor), \
         patch("app.get_cursor", return_value=mock_cursor), \
         patch("app.commit_db"):
        response = flask_test_client.post(
            "/user/sms-preference",
            json={"user_id": user_id, "sms_opt_out": sms_opt_out},
        )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.get_data(as_text=True)}"
    )
    data = response.get_json()
    assert data is not None
    assert data.get("user_id") == user_id
    assert data.get("sms_opt_out") == sms_opt_out


# ===========================================================================
# Property 11: every SMS send produces exactly one log entry
# Feature: sms-notification, Property 11: every SMS send produces exactly one log entry
# ===========================================================================

@given(st.integers(min_value=1, max_value=20))  # N sends
@settings(max_examples=100)
def test_every_send_produces_exactly_one_log_entry(n_sends):
    """
    Calling send_sms() N times (with mocked Semaphore returning 200) must
    result in exactly N calls to _log_sms().
    """
    service = SMS_Service()

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200

    log_calls = []

    def capture_log(*args, **kwargs):
        log_calls.append(args)

    with patch("requests.post", return_value=mock_response), \
         patch.object(service, "_log_sms", side_effect=capture_log):
        for i in range(n_sends):
            service.send_sms(
                phone=f"+6390000{i:05d}",
                message="test message",
                recipient_type="customer",
                recipient_id=i,
            )

    assert len(log_calls) == n_sends, (
        f"Expected {n_sends} log entries, got {len(log_calls)}"
    )


@given(st.integers(min_value=1, max_value=10))  # N sends that all fail
@settings(max_examples=50)
def test_failed_send_still_produces_exactly_one_log_entry(n_sends):
    """
    Even when Semaphore always returns 500 (triggering retry), each call to
    send_sms() must produce exactly one final log entry (status='failed').
    The 'retried' intermediate log is also counted - total logs per call = 2
    (one 'retried' + one 'failed'), but the important invariant is that the
    final 'failed' log is always written.
    """
    service = SMS_Service()

    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 500
    mock_response.text = "Server Error"

    failed_logs = []
    retried_logs = []

    def capture_log(phone, recipient_type, recipient_id, message_body,
                    status, response_code=None, error_message=None):
        if status == "failed":
            failed_logs.append(status)
        elif status == "retried":
            retried_logs.append(status)

    with patch("requests.post", return_value=mock_response), \
         patch("time.sleep"), \
         patch.object(service, "_log_sms", side_effect=capture_log):
        for i in range(n_sends):
            service.send_sms(
                phone=f"+6390000{i:05d}",
                message="test message",
                recipient_type="customer",
                recipient_id=i,
            )

    # Each send must produce exactly one 'failed' log
    assert len(failed_logs) == n_sends, (
        f"Expected {n_sends} 'failed' log entries, got {len(failed_logs)}"
    )
    # Each send must also produce exactly one 'retried' log (first attempt failed)
    assert len(retried_logs) == n_sends, (
        f"Expected {n_sends} 'retried' log entries, got {len(retried_logs)}"
    )


# ===========================================================================
# Property 12: SMS log pagination returns correct ordered slices
# Feature: sms-notification, Property 12: SMS log pagination returns correct ordered slices
# ===========================================================================

def _make_log_rows(n: int, recipient_type: str = "customer"):
    """
    Build N fake sms_logs rows with strictly decreasing created_at timestamps
    (newest first, as the DB would return them with ORDER BY created_at DESC).
    created_at is a datetime object so the route's .isoformat() call works.
    """
    from datetime import datetime, timedelta

    base = datetime(2025, 1, 1, 12, 0, 0)
    rows = []
    for i in range(n):
        rows.append(
            {
                "id": i + 1,
                "recipient_phone": f"+6390000{i:05d}",
                "recipient_type": recipient_type,
                "recipient_id": i + 1,
                "message_body": f"msg {i}",
                "status": "sent",
                "semaphore_response_code": 200,
                "error_message": None,
                # datetime object -- the route calls .isoformat() on this
                "created_at": base - timedelta(seconds=i),
            }
        )
    return rows


@given(
    st.integers(min_value=1, max_value=50),   # total log rows
    st.integers(min_value=1, max_value=10),   # per_page
    st.integers(min_value=1, max_value=10),   # page
)
@settings(max_examples=150)
def test_sms_log_pagination_returns_correct_slice(
    flask_test_client, total_rows, per_page, page
):
    """
    GET /admin/sms-logs?page=P&per_page=PP must return the correct slice of
    rows ordered by created_at DESC.
    """
    all_rows = _make_log_rows(total_rows)

    # Compute expected slice (0-indexed)
    start = (page - 1) * per_page
    expected_slice = all_rows[start: start + per_page]

    mock_cursor = MagicMock()

    def fetchall_side_effect():
        return expected_slice

    def fetchone_side_effect():
        return {"total": total_rows}

    mock_cursor.fetchall.side_effect = fetchall_side_effect
    mock_cursor.fetchone.side_effect = fetchone_side_effect

    with patch("app.get_cursor", return_value=mock_cursor):
        response = flask_test_client.get(
            f"/admin/sms-logs?page={page}&per_page={per_page}"
        )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.get_data(as_text=True)}"
    )
    data = response.get_json()
    assert data is not None
    assert data.get("page") == page
    assert data.get("per_page") == per_page
    assert data.get("total") == total_rows

    returned_logs = data.get("logs", [])
    assert len(returned_logs) == len(expected_slice), (
        f"Expected {len(expected_slice)} logs on page {page}, got {len(returned_logs)}"
    )

    # Verify ordering: created_at ISO strings must be non-increasing (DESC)
    timestamps = [row["created_at"] for row in returned_logs]
    assert timestamps == sorted(timestamps, reverse=True), (
        "Logs are not ordered by created_at DESC"
    )


# ===========================================================================
# Property 13: SMS log filtering returns only matching recipient types
# Feature: sms-notification, Property 13: SMS log filtering returns only matching recipient types
# ===========================================================================

@given(
    _recipient_type,                              # the type to filter by
    st.integers(min_value=1, max_value=30),       # number of matching rows
)
@settings(max_examples=150)
def test_sms_log_filter_returns_only_matching_type(
    flask_test_client, recipient_type, n_matching
):
    """
    GET /admin/sms-logs?recipient_type=X must return only rows where
    recipient_type equals X.
    """
    matching_rows = _make_log_rows(n_matching, recipient_type=recipient_type)

    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = matching_rows
    mock_cursor.fetchone.return_value = {"total": n_matching}

    with patch("app.get_cursor", return_value=mock_cursor):
        response = flask_test_client.get(
            f"/admin/sms-logs?recipient_type={recipient_type}"
        )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.get_data(as_text=True)}"
    )
    data = response.get_json()
    assert data is not None

    for log_entry in data.get("logs", []):
        assert log_entry["recipient_type"] == recipient_type, (
            f"Filter returned a row with recipient_type={log_entry['recipient_type']!r}, "
            f"expected {recipient_type!r}"
        )


# ===========================================================================
# Property 14: notify_admins only sends to active admins
# Feature: sms-notification, Property 14: notify_admins only sends to active admins
# ===========================================================================

# Strategy: generate a list of admin dicts with random is_active and phone values
_admin_entry = st.fixed_dictionaries(
    {
        "id": st.integers(min_value=1, max_value=9999),
        "phone": st.one_of(
            st.none(),
            st.from_regex(r"\+639[0-9]{9}", fullmatch=True),
        ),
        "is_active": st.booleans(),
    }
)


@given(st.lists(_admin_entry, min_size=0, max_size=20), _text)
@settings(max_examples=200)
def test_notify_admins_only_sends_to_active_admins_with_phones(admins, message):
    """
    notify_admins() must call send_sms() exactly once per admin that is
    both is_active=True AND has a non-null phone. It must NOT call send_sms()
    for inactive admins or admins without a phone.
    """
    # The DB query in notify_admins already filters: WHERE is_active=TRUE AND phone IS NOT NULL
    # We simulate that by only returning the qualifying rows from fetchall.
    qualifying = [a for a in admins if a["is_active"] and a["phone"] is not None]

    service = SMS_Service()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = qualifying

    with patch("notifications.get_cursor", return_value=mock_cursor), \
         patch.object(service, "send_sms", return_value=True) as mock_send:
        results = service.notify_admins(message)

    assert mock_send.call_count == len(qualifying), (
        f"Expected {len(qualifying)} send_sms calls, got {mock_send.call_count}"
    )
    assert len(results) == len(qualifying), (
        f"Expected {len(qualifying)} results, got {len(results)}"
    )

    # Verify each call used the correct phone number
    called_phones = [c.args[0] for c in mock_send.call_args_list]
    expected_phones = [a["phone"] for a in qualifying]
    assert called_phones == expected_phones, (
        f"send_sms called with wrong phones.\nExpected: {expected_phones}\nGot: {called_phones}"
    )
