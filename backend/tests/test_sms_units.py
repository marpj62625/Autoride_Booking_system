"""
Example-based unit tests for the SMS Notification feature.

Feature: sms-notification
Task 9: Unit tests (example-based)
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Path setup
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

from notifications import (  # noqa: E402
    compose_booking_rejected_sms,
    compose_completed_sms,
    compose_license_approved_sms,
    compose_license_rejected_sms,
    SMS_Service,
)


# ---------------------------------------------------------------------------
# Flask test client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def flask_test_client():
    """
    Create a Flask test client with all external dependencies mocked so the
    app can be imported and exercised without a live DB or Semaphore API.
    """
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


# ===========================================================================
# 9.1 — compose_booking_rejected_sms() contains booking ID and support text
# ===========================================================================

def test_compose_booking_rejected_sms_contains_booking_id_and_support():
    """compose_booking_rejected_sms(42) must contain '42' and 'support'."""
    result = compose_booking_rejected_sms(42)
    assert "42" in result
    assert "support" in result.lower()


# ===========================================================================
# 9.2 — compose_completed_sms() contains booking ID and thank-you text
# ===========================================================================

def test_compose_completed_sms_contains_booking_id_and_thank_you():
    """compose_completed_sms(99) must contain '99' and 'thank'."""
    result = compose_completed_sms(99)
    assert "99" in result
    assert "thank" in result.lower()


# ===========================================================================
# 9.3 — compose_license_approved_sms() contains "verified" and "book vehicles"
# ===========================================================================

def test_compose_license_approved_sms_contains_verified_and_book_vehicles():
    """compose_license_approved_sms() must contain 'verified' and 'book vehicles'."""
    result = compose_license_approved_sms()
    assert "verified" in result.lower()
    assert "book vehicles" in result.lower()


# ===========================================================================
# 9.4 — compose_license_rejected_sms() contains "not approved" and "re-upload"
# ===========================================================================

def test_compose_license_rejected_sms_contains_not_approved_and_reupload():
    """compose_license_rejected_sms() must contain 'not approved' and 're-upload'."""
    result = compose_license_rejected_sms()
    assert "not approved" in result.lower()
    assert "re-upload" in result.lower()


# ===========================================================================
# 9.5 — send_sms() with mocked Semaphore returning 200
# ===========================================================================

def test_send_sms_success_logs_sent_returns_true_api_called_once():
    """
    When Semaphore returns 200, send_sms() must:
    - return True
    - call requests.post exactly once
    - call _log_sms once with status='sent'
    """
    service = SMS_Service()

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200

    log_calls = []

    def capture_log(*args, **kwargs):
        log_calls.append(kwargs if kwargs else {"args": args})

    with patch("requests.post", return_value=mock_response) as mock_post, \
         patch.object(service, "_log_sms", side_effect=capture_log):
        result = service.send_sms("+639123456789", "hello", "customer", 1)

    assert result is True
    mock_post.assert_called_once()
    assert len(log_calls) == 1
    # The status is passed as a positional arg (5th arg: phone, type, id, body, status)
    # Check via the captured args
    assert log_calls[0].get("args", (None,) * 5)[4] == "sent" or \
           _extract_status_from_log_call(service, "+639123456789", "hello", "customer", 1,
                                         mock_response) == "sent"


def _extract_status_from_log_call(service, phone, message, recipient_type, recipient_id, mock_response):
    """Helper to verify _log_sms is called with status='sent'."""
    log_statuses = []

    def capture(p, rt, rid, body, status, response_code=None, error_message=None):
        log_statuses.append(status)

    with patch("requests.post", return_value=mock_response), \
         patch.object(service, "_log_sms", side_effect=capture):
        service.send_sms(phone, message, recipient_type, recipient_id)

    return log_statuses[0] if log_statuses else None


# Cleaner version of 9.5 using explicit keyword capture
def test_send_sms_success_status_is_sent():
    """Verify _log_sms is called with status='sent' on a 200 response."""
    service = SMS_Service()

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200

    log_statuses = []

    def capture(phone, recipient_type, recipient_id, message_body,
                status, response_code=None, error_message=None):
        log_statuses.append(status)

    with patch("requests.post", return_value=mock_response) as mock_post, \
         patch.object(service, "_log_sms", side_effect=capture):
        result = service.send_sms("+639123456789", "hello", "customer", 1)

    assert result is True
    assert mock_post.call_count == 1
    assert log_statuses == ["sent"]


# ===========================================================================
# 9.6 — send_sms() with mocked Semaphore always returning 500
# ===========================================================================

def test_send_sms_always_fails_logs_retried_then_failed_api_called_twice():
    """
    When Semaphore always returns 500, send_sms() must:
    - return False
    - call requests.post exactly twice (initial + retry)
    - call _log_sms twice: once with status='retried', once with status='failed'
    """
    service = SMS_Service()

    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 500
    mock_response.text = "Server Error"

    log_statuses = []

    def capture(phone, recipient_type, recipient_id, message_body,
                status, response_code=None, error_message=None):
        log_statuses.append(status)

    with patch("requests.post", return_value=mock_response) as mock_post, \
         patch("time.sleep"), \
         patch.object(service, "_log_sms", side_effect=capture):
        result = service.send_sms("+639123456789", "hello", "customer", 1)

    assert result is False
    assert mock_post.call_count == 2
    assert len(log_statuses) == 2
    assert "retried" in log_statuses
    assert "failed" in log_statuses


# ===========================================================================
# 9.7 — send_sms() with mocked Semaphore failing then succeeding
# ===========================================================================

def test_send_sms_fail_then_succeed_logs_retried_then_sent_api_called_twice():
    """
    When Semaphore returns 500 on first call and 200 on second, send_sms() must:
    - return True
    - call requests.post exactly twice
    - call _log_sms twice: first with status='retried', second with status='sent'
    """
    service = SMS_Service()

    mock_fail = MagicMock()
    mock_fail.ok = False
    mock_fail.status_code = 500
    mock_fail.text = "Server Error"

    mock_success = MagicMock()
    mock_success.ok = True
    mock_success.status_code = 200

    log_statuses = []

    def capture(phone, recipient_type, recipient_id, message_body,
                status, response_code=None, error_message=None):
        log_statuses.append(status)

    with patch("requests.post", side_effect=[mock_fail, mock_success]) as mock_post, \
         patch("time.sleep"), \
         patch.object(service, "_log_sms", side_effect=capture):
        result = service.send_sms("+639123456789", "hello", "customer", 1)

    assert result is True
    assert mock_post.call_count == 2
    assert len(log_statuses) == 2
    assert log_statuses[0] == "retried"
    assert log_statuses[1] == "sent"


# ===========================================================================
# 9.8 — POST /user/sms-preference with valid data — 200 response, DB updated
# ===========================================================================

def test_sms_preference_valid_data_returns_200_and_updates_db(flask_test_client):
    """
    POST /user/sms-preference with valid JSON must return 200 and the
    response body must echo back user_id and sms_opt_out. The cursor's
    execute must have been called with an UPDATE statement.
    """
    mock_cursor = MagicMock()
    # Simulate user found on SELECT
    mock_cursor.fetchone.return_value = {"id": 1}

    execute_calls = []

    def capture_execute(sql, params=None):
        execute_calls.append(sql)

    mock_cursor.execute.side_effect = capture_execute

    with patch("app.get_cursor", return_value=mock_cursor), \
         patch("app.commit_db"):
        response = flask_test_client.post(
            "/user/sms-preference",
            json={"user_id": 1, "sms_opt_out": True},
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data.get("user_id") == 1
    assert data.get("sms_opt_out") is True

    # Verify an UPDATE statement was executed
    update_calls = [sql for sql in execute_calls if "UPDATE" in sql.upper()]
    assert len(update_calls) >= 1, "Expected at least one UPDATE execute call"


# ===========================================================================
# 9.9 — POST /user/sms-preference with missing fields — 400 response
# ===========================================================================

def test_sms_preference_missing_sms_opt_out_returns_400(flask_test_client):
    """POST /user/sms-preference with missing sms_opt_out must return 400."""
    response = flask_test_client.post(
        "/user/sms-preference",
        json={"user_id": 1},
    )
    assert response.status_code == 400


def test_sms_preference_empty_body_returns_400(flask_test_client):
    """POST /user/sms-preference with empty JSON must return 400."""
    response = flask_test_client.post(
        "/user/sms-preference",
        json={},
    )
    assert response.status_code == 400


# ===========================================================================
# 9.10 — GET /admin/sms-logs with no filters — returns records ordered by
#         created_at DESC
# ===========================================================================

def test_get_sms_logs_no_filters_returns_ordered_records(flask_test_client):
    """
    GET /admin/sms-logs must return 200 with 'logs' containing 3 entries
    ordered by created_at DESC.
    """
    base = datetime(2025, 6, 1, 12, 0, 0)
    fake_rows = [
        {
            "id": 1,
            "recipient_phone": "+639000000001",
            "recipient_type": "customer",
            "recipient_id": 1,
            "message_body": "msg 0",
            "status": "sent",
            "semaphore_response_code": 200,
            "error_message": None,
            "created_at": base,                          # newest
        },
        {
            "id": 2,
            "recipient_phone": "+639000000002",
            "recipient_type": "customer",
            "recipient_id": 2,
            "message_body": "msg 1",
            "status": "sent",
            "semaphore_response_code": 200,
            "error_message": None,
            "created_at": base - timedelta(seconds=60),  # middle
        },
        {
            "id": 3,
            "recipient_phone": "+639000000003",
            "recipient_type": "customer",
            "recipient_id": 3,
            "message_body": "msg 2",
            "status": "sent",
            "semaphore_response_code": 200,
            "error_message": None,
            "created_at": base - timedelta(seconds=120), # oldest
        },
    ]

    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = fake_rows
    mock_cursor.fetchone.return_value = {"total": 3}

    with patch("app.get_cursor", return_value=mock_cursor):
        response = flask_test_client.get("/admin/sms-logs")

    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert "logs" in data
    assert len(data["logs"]) == 3

    # Verify created_at values are in descending order
    timestamps = [entry["created_at"] for entry in data["logs"]]
    assert timestamps == sorted(timestamps, reverse=True), (
        f"Logs are not ordered by created_at DESC: {timestamps}"
    )
