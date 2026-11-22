"""Offline checks for the rolling Homework 7 monitor."""

from __future__ import annotations

import json
import sys

import pytest

from monitoring import run


def _trace(trace_id: str, session_id: str | None, model: str, role: str, text: str, time: str):
    return {
        "id": trace_id,
        "timestamp": time,
        "models": [model],
        "meta": {"session_id": session_id} if session_id else {},
        "trace": [{"role": role, "text": text}],
        "text": f"{role}: {text}",
    }


def test_daily_groups_turns_by_session_and_excludes_other_models():
    traces = [
        _trace("second", "session-a", "gpt-4o-mini-2024-07-18", "assistant", "done", "2026-01-01T01:00:00Z"),
        _trace("first", "session-a", "gpt-4o-mini-2024-07-18", "user", "help", "2026-01-01T00:00:00Z"),
        _trace("other", "session-b", "different-model", "user", "hello", "2026-01-01T00:00:00Z"),
        _trace("no-session", None, "gpt-4o-mini-2024-07-18", "user", "hello", "2026-01-01T00:00:00Z"),
    ]

    conversations = run.build_session_conversations(traces, "gpt-4o-mini-2024-07-18")

    assert len(conversations) == 1
    assert conversations[0]["id"] == "second"
    assert conversations[0]["text"] == "user: help\nassistant: done"
    assert conversations[0]["turn_count"] == 1


def test_daily_empty_window_records_zero_without_judging(tmp_path, monkeypatch):
    import langfuse

    config = {
        "judge_id": "unnecessary_messages_or_details-v13",
        "judge_mode": "unnecessary_messages_or_details",
        "model": "gpt-4o-mini",
        "random_rate": 0.2,
        "risk_groups": ["policy_lookup"],
        "threshold": 0.15,
        "periods": [],
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    monkeypatch.setattr(run, "CONFIG", config_path)
    monkeypatch.setattr(run, "ROOT", tmp_path)
    monkeypatch.setattr(run, "HISTORY", tmp_path / "history.jsonl")
    monkeypatch.setattr(run, "CHART", tmp_path / "prevalence.svg")
    monkeypatch.setattr(run, "load_env", lambda: None)
    monkeypatch.setattr(langfuse, "Langfuse", lambda: object())
    monkeypatch.setattr(run, "fetch_period_traces", lambda *_: [])
    monkeypatch.setattr(run, "judge_sample", lambda *_: (_ for _ in ()).throw(AssertionError("judge called")))
    monkeypatch.setattr(sys, "argv", ["monitoring.run", "--last-hours", "24"])

    run.main()

    row = json.loads((tmp_path / "history.jsonl").read_text())
    status = json.loads((tmp_path / "monitoring/results/run-status.json").read_text())
    assert row["conversation_count"] == 0
    assert row["random_sample_count"] == 0
    assert status["status"] == "no_eligible_conversations"
    assert status["judge_calls"] == 0


def test_daily_rejects_changed_call_count_before_judging(tmp_path, monkeypatch):
    import langfuse

    config = {
        "judge_id": "unnecessary_messages_or_details-v13",
        "judge_mode": "unnecessary_messages_or_details",
        "model": "gpt-4o-mini",
        "observed_model": "gpt-4o-mini-2024-07-18",
        "random_rate": 0.2,
        "risk_groups": ["policy_lookup"],
        "threshold": 0.15,
        "periods": [],
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    monkeypatch.setattr(run, "CONFIG", config_path)
    monkeypatch.setattr(run, "ROOT", tmp_path)
    monkeypatch.setattr(run, "load_env", lambda: None)
    monkeypatch.setattr(langfuse, "Langfuse", lambda: object())
    monkeypatch.setattr(run, "fetch_period_traces", lambda *_: [
        _trace("trace-1", "session-1", "gpt-4o-mini-2024-07-18", "user", "help", "2026-01-01T00:00:00Z")
    ])
    monkeypatch.setattr(run, "judge_sample", lambda *_: (_ for _ in ()).throw(AssertionError("judge called")))
    monkeypatch.setattr(sys, "argv", [
        "monitoring.run", "--last-hours", "24", "--as-of", "2026-01-02T00:00:00Z",
        "--expected-judge-calls", "0",
    ])

    with pytest.raises(ValueError, match="changed since approval"):
        run.main()
