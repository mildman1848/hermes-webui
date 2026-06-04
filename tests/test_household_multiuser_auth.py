"""Regression tests for household multi-user WebUI auth/session context."""

from __future__ import annotations


def test_household_owner_context_goes_to_ephemeral_system_prompt_not_prefill():
    from api.streaming import (
        _prefill_messages_with_webui_context,
        _webui_ephemeral_system_prompt,
    )

    prefill = {"messages": [{"role": "user", "content": "remember this"}]}

    messages = _prefill_messages_with_webui_context(prefill, {}, owner="jacky")
    prompt = _webui_ephemeral_system_prompt(None, config_data={}, owner="jacky")

    assert messages == [{"role": "user", "content": "remember this"}]
    assert "Authenticated WebUI user" in prompt
    assert "`jacky`" in prompt
    assert "For Jacky" in prompt


def test_household_owner_context_is_omitted_without_owner():
    from api.streaming import _webui_ephemeral_system_prompt

    prompt = _webui_ephemeral_system_prompt(None, config_data={}, owner=None)

    assert "Authenticated WebUI user" not in prompt


def test_auth_session_tracks_normalized_username(monkeypatch, tmp_path):
    from api import auth

    sessions_file = tmp_path / ".sessions.json"
    monkeypatch.setattr(auth, "_SESSIONS_FILE", sessions_file)
    monkeypatch.setattr(auth, "_sessions", {})
    monkeypatch.setattr(auth, "_session_users", {})
    monkeypatch.setattr(auth, "_save_sessions", lambda sessions: None)

    cookie = auth.create_session("DOMAIN\\Jacky@example.invalid")

    assert auth.verify_session(cookie) is True
    assert auth.username_for_cookie(cookie) == "jacky"


def test_multi_user_visibility_filters_by_owner(monkeypatch):
    import api.routes as routes

    sessions = [
        {"session_id": "a", "owner": "philipp"},
        {"session_id": "b", "owner": "jacky"},
        {"session_id": "legacy"},
    ]

    monkeypatch.setenv("HERMES_WEBUI_DEFAULT_USER", "philipp")
    monkeypatch.setattr(routes, "_current_webui_user", lambda handler: "jacky")

    assert routes._filter_sessions_for_current_user(object(), sessions) == [sessions[1]]
