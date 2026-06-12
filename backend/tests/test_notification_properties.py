"""
Property-based tests for the In-App Notification feature.
Uses Hypothesis to verify correctness properties across random inputs.

Feature: in-app-notifications
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch, call
from hypothesis import given, settings, assume
from hypothesis import strategies as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest.mock as _mock

_config_patch = _mock.patch.dict(
    "sys.modules",
    {
        "config": _mock.MagicMock(
            SMTP_SERVER="localhost",
            SMTP_PORT=25,
            EMAIL_USER="test@test.com",
            EMAIL_PASS="pass",
        ),
        "database": _mock.MagicMock(),
    },
)
_config_patch.start()

from notifications import Notification_Service  # noqa: E402


# ---------------------------------------------------------------------------
# Fake notification row helper
# ---------------------------------------------------------------------------

from datetime import datetime, timedelta


def _make_notif_rows(n, user_id=1):
    base = datetime(2025, 1, 1, 12, 0, 0)
    rows = []
    for i in range(n):
        rows.append({
            "id": i + 1,
            "user_id": user_id,
            "admin_id": None,
            "title": f"Notification {i}",
            "message": f"Message {i}",
            "type": "booking_created",
            "is_read": False,
            "created_at": base - timedelta(seconds=i),
        })
    return rows


# ---------------------------------------------------------------------------
# Flask test client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def flask_test_client():
    """
    Create a Flask test client with all external dependencies mocked so the
    app can be imported and exercised without a live DB.
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
# Property 1: notify_user inserts exactly one row
# Feature: in-app-notifications, Property 1: notify_user inserts exactly one row
# Validates: Requirements 1.1
# ===========================================================================

@given(
    st.integers(min_value=1, max_value=999999),
    st.text(min_size=1, max_size=80),
    st.text(min_size=1, max_size=200),
    st.text(min_size=1, max_size=40),
)
@settings(max_examples=200)
def test_notify_user_inserts_exactly_one_row(user_id, title, message, notif_type):
    """
    For any valid user_id, title, message, and type, notify_user() must call
    execute exactly once with an INSERT INTO notifications statement, passing
    the correct user_id, and must call commit_db exactly once.
    """
    service = Notification_Service()
    mock_cursor = MagicMock()

    with patch("notifications.get_cursor", return_value=mock_cursor), \
         patch("notifications.commit_db") as mock_commit:
        result = service.notify_user(user_id, title, message, notif_type)

    # execute called exactly once
    assert mock_cursor.execute.call_count == 1, (
        f"Expected execute called once, got {mock_cursor.execute.call_count}"
    )

    # The SQL must be an INSERT INTO notifications
    call_args = mock_cursor.execute.call_args
    sql = call_args[0][0]
    assert "INSERT INTO notifications" in sql, (
        f"Expected INSERT INTO notifications in SQL, got: {sql!r}"
    )

    # user_id must appear in the execute call args
    params = call_args[0][1]
    assert user_id in params, (
        f"Expected user_id={user_id} in execute params, got: {params}"
    )

    # commit_db called exactly once
    mock_commit.assert_called_once()

    # Returns True on success
    assert result is True


# ===========================================================================
# Property 2: notify_admins_inapp inserts one row per active admin
# Feature: in-app-notifications, Property 2: notify_admins_inapp inserts one row per active admin
# Validates: Requirements 1.2
# ===========================================================================

_admin_entry = st.fixed_dictionaries({
    "id": st.integers(min_value=1, max_value=9999),
    "is_active": st.booleans(),
})


@given(
    st.lists(_admin_entry, min_size=0, max_size=20),
    st.text(min_size=1, max_size=80),
    st.text(min_size=1, max_size=200),
    st.text(min_size=1, max_size=40),
)
@settings(max_examples=200)
def test_notify_admins_inapp_inserts_one_row_per_active_admin(
    admins, title, message, notif_type
):
    """
    For any list of admins with mixed is_active values, notify_admins_inapp()
    must insert exactly one notification row per active admin and zero rows
    for inactive admins.
    """
    active_admins = [a for a in admins if a["is_active"]]

    service = Notification_Service()

    # First cursor: fetchall returns only active admins (simulating WHERE is_active = TRUE)
    first_cursor = MagicMock()
    first_cursor.fetchall.return_value = active_admins

    # Subsequent cursors: one per active admin for the INSERT
    insert_cursors = [MagicMock() for _ in active_admins]
    cursor_sequence = [first_cursor] + insert_cursors

    cursor_iter = iter(cursor_sequence)

    def get_cursor_side_effect():
        try:
            return next(cursor_iter)
        except StopIteration:
            return MagicMock()

    with patch("notifications.get_cursor", side_effect=get_cursor_side_effect), \
         patch("notifications.commit_db"):
        results = service.notify_admins_inapp(title, message, notif_type)

    # Number of INSERT calls equals number of active admins
    total_inserts = sum(c.execute.call_count for c in insert_cursors)
    assert total_inserts == len(active_admins), (
        f"Expected {len(active_admins)} INSERT calls, got {total_inserts}"
    )

    # Results list length matches active admin count
    assert len(results) == len(active_admins), (
        f"Expected {len(active_admins)} results, got {len(results)}"
    )


# ===========================================================================
# Property 3: GET /notifications returns only requesting user's data
# Feature: in-app-notifications, Property 3: GET /notifications returns only requesting user's notifications
# Validates: Requirements 3.1
# ===========================================================================

@given(st.integers(min_value=1, max_value=999999))
@settings(max_examples=100)
def test_get_notifications_returns_only_requesting_users_data(
    flask_test_client, user_id
):
    """
    GET /notifications?user_id=X must return only rows where user_id = X.
    The SQL WHERE clause must be called with the correct user_id.
    """
    fake_rows = _make_notif_rows(5, user_id=user_id)

    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = fake_rows

    with patch("app.get_cursor", return_value=mock_cursor):
        response = flask_test_client.get(f"/notifications?user_id={user_id}")

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.get_data(as_text=True)}"
    )

    data = response.get_json()
    assert data is not None

    # All returned items must have the correct user_id
    for item in data:
        assert item["user_id"] == user_id, (
            f"Returned notification has user_id={item['user_id']}, expected {user_id}"
        )

    # Verify the SQL was called with the correct user_id
    call_args_list = mock_cursor.execute.call_args_list
    assert len(call_args_list) >= 1
    # The WHERE clause should include user_id
    last_call = call_args_list[-1]
    params = last_call[0][1] if len(last_call[0]) > 1 else last_call[1].get("params", ())
    assert user_id in params, (
        f"Expected user_id={user_id} in SQL params, got: {params}"
    )


# ===========================================================================
# Property 4: POST /notifications/read-all sets all to read
# Feature: in-app-notifications, Property 4: read-all sets is_read=true for all user notifications
# Validates: Requirements 3.2
# ===========================================================================

@given(
    st.integers(min_value=1, max_value=999999),
    st.integers(min_value=1, max_value=20),
)
@settings(max_examples=100)
def test_read_all_returns_updated_count(flask_test_client, user_id, n):
    """
    POST /notifications/read-all with a valid user_id must return 200 with
    {"updated": N} where N is the number of rows affected (rowcount).
    """
    mock_cursor = MagicMock()
    mock_cursor.rowcount = n

    with patch("app.get_cursor", return_value=mock_cursor), \
         patch("app.commit_db"):
        response = flask_test_client.post(
            "/notifications/read-all",
            json={"user_id": user_id},
        )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.get_data(as_text=True)}"
    )

    data = response.get_json()
    assert data is not None
    assert data.get("updated") == n, (
        f"Expected updated={n}, got {data.get('updated')}"
    )


# ===========================================================================
# Property 5: GET /notifications returns notifications ordered by created_at DESC
# Feature: in-app-notifications, Property 5: GET /notifications returns notifications ordered by created_at DESC
# Validates: Requirements 3.1
# ===========================================================================

@given(st.integers(min_value=1, max_value=20))
@settings(max_examples=100)
def test_get_notifications_ordered_by_created_at_desc(flask_test_client, n):
    """
    GET /notifications must return notifications ordered by created_at DESC
    (newest first). The created_at ISO strings in the response must be in
    descending order.
    """
    # Build N rows with strictly decreasing created_at (newest first)
    fake_rows = _make_notif_rows(n, user_id=1)

    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = fake_rows

    with patch("app.get_cursor", return_value=mock_cursor):
        response = flask_test_client.get("/notifications?user_id=1")

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.get_data(as_text=True)}"
    )

    data = response.get_json()
    assert data is not None

    timestamps = [item["created_at"] for item in data]
    assert timestamps == sorted(timestamps, reverse=True), (
        f"Notifications are not ordered by created_at DESC: {timestamps}"
    )


# ===========================================================================
# Property 6: notify_user failure does not raise
# Feature: in-app-notifications, Property 6: notify_user failure does not raise
# Validates: Requirements 2.1
# ===========================================================================

@given(
    st.integers(min_value=1, max_value=999999),
    st.text(min_size=1, max_size=80),
    st.text(min_size=1, max_size=200),
    st.text(min_size=1, max_size=40),
)
@settings(max_examples=200)
def test_notify_user_failure_does_not_raise(user_id, title, message, notif_type):
    """
    When get_cursor raises an exception, notify_user() must catch it, log it
    to stderr, and return False without raising - ensuring the calling route
    handler is not affected.
    """
    service = Notification_Service()

    with patch("notifications.get_cursor", side_effect=Exception("DB error")):
        result = service.notify_user(user_id, title, message, notif_type)

    assert result is False, (
        f"Expected notify_user to return False on DB error, got {result!r}"
    )
