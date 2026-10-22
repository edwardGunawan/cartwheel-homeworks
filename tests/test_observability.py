"""Offline authentication checks for the Homework 2 endpoint."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from server import app as server_app


@pytest.fixture(autouse=True)
def clear_sessions() -> None:
    """Keep the in-memory session registry isolated between tests."""
    server_app._SESSIONS.clear()
    yield
    server_app._SESSIONS.clear()


def test_session_creation_rejects_claimed_role_that_differs_from_database(
    world: dict,
) -> None:
    """Shopper 1 cannot claim to be a merchant."""
    with pytest.raises(HTTPException) as exc_info:
        server_app.create_session(
            server_app.SessionCreate(user_id=1, role="merchant")
        )

    assert exc_info.value.status_code == 403


def test_token_cannot_authorize_a_different_session(world: dict) -> None:
    """A valid token is bound to the session that issued it."""
    first = server_app.create_session(server_app.SessionCreate(user_id=1, role="shopper"))
    second = server_app.create_session(server_app.SessionCreate(user_id=2, role="shopper"))

    with pytest.raises(HTTPException) as exc_info:
        server_app._authorize(second["session_id"], f"Bearer {first['token']}")

    assert exc_info.value.status_code == 403
