"""Build and judge one Homework 7 monitoring period from Langfuse traces."""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from analysis.helpers.normalization import normalize_trace
from monitoring.chart import prevalence_chart
from monitoring.correct import corrected_mode_prevalence
from monitoring.run_judges import judge_sample, judge_test_data, load_monitoring_judge
from monitoring.sample import DEFAULT_RISK_GROUPS, select_traces
from monitoring.write_scores import build_score_records, post_scores
from observability.instrument import load_env
from scenarios.export_langfuse import _jsonable, _scenario_id

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "monitoring" / "config.json"
SCENARIOS = ROOT / "scenarios" / "monitoring_scenarios.jsonl"
HISTORY = ROOT / "monitoring" / "history.jsonl"
CHART = ROOT / "monitoring" / "prevalence.svg"


def _utc_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("monitoring periods need UTC timestamps")
    return parsed


def _scenario_turns() -> dict[str, int]:
    rows = [json.loads(line) for line in SCENARIOS.read_text().splitlines() if line.strip()]
    turns = {row["id"]: 1 + len(row.get("followups") or []) for row in rows}
    if len(rows) != 50 or len(turns) != 50:
        raise ValueError("monitoring_scenarios.jsonl must have 50 unique scenario ids")
    return turns


def fetch_period_traces(period: dict[str, str], scenario_ids: set[str] | None, client: Any) -> list[dict[str, Any]]:
    """Fetch complete eligible traces; list responses omit tool evidence."""
    start, end = _utc_time(period["from"]), _utc_time(period["to"])
    if start >= end:
        raise ValueError("period start must precede its end")
    traces = []
    page = 1
    while True:
        batch = list(
            client.api.trace.list(
                page=page, limit=100, from_timestamp=start, to_timestamp=end
            ).data or []
        )
        for summary in batch:
            raw = _jsonable(client.api.trace.get(summary.id))
            scenario_id = _scenario_id(raw) if scenario_ids is not None else None
            if scenario_ids is None or scenario_id in scenario_ids:
                raw["cartwheel_scenario_id"] = scenario_id
                traces.append(normalize_trace(raw))
        if len(batch) < 100:
            return traces
        page += 1


def build_conversations(
    traces: list[dict[str, Any]], scenario_turns: dict[str, int], observed_model: str
) -> list[dict[str, Any]]:
    """Require one complete run per scenario and keep HW5-style trace text."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    trace_ids = set()
    for trace in traces:
        scenario_id = trace["meta"].get("scenario_id")
        if scenario_id not in scenario_turns:
            raise ValueError(f"unexpected scenario id {scenario_id!r}")
        if trace["id"] in trace_ids:
            raise ValueError(f"duplicate trace id {trace['id']}")
        trace_ids.add(trace["id"])
        if set(trace["models"]) != {observed_model}:
            raise ValueError(f"{scenario_id}: Cartwheel model does not match {observed_model}")
        groups[scenario_id].append(trace)

    missing = scenario_turns.keys() - groups.keys()
    if missing:
        raise ValueError(f"period is missing {len(missing)} scenarios: {sorted(missing)[:5]}")

    conversations = []
    for scenario_id, expected_turns in scenario_turns.items():
        group = sorted(groups[scenario_id], key=lambda trace: (trace["timestamp"], trace["id"]))
        sessions = {trace["meta"].get("session_id") for trace in group}
        if None in sessions or len(sessions) != 1 or len(group) != expected_turns:
            raise ValueError(f"{scenario_id}: period contains a missing turn or a separate retry")
        messages = [message for trace in group for message in trace["trace"]]
        user_turns = sum(message.get("role") == "user" for message in messages)
        if user_turns != expected_turns:
            raise ValueError(f"{scenario_id}: expected {expected_turns} user turns, got {user_turns}")
        text = "\n".join(trace["text"] for trace in group if trace["text"])
        if not text.strip():
            raise ValueError(f"{scenario_id}: conversation has no judge input")
        conversations.append(
            {
                "id": group[-1]["id"],
                "text": text,
                "tools": [
                    message["name"]
                    for message in messages
                    if message.get("role") == "tool_call" and message.get("name")
                ],
                "turn_count": user_turns,
            }
        )
    return conversations


def build_session_conversations(
    traces: list[dict[str, Any]], observed_model: str
) -> list[dict[str, Any]]:
    """Group eligible live Cartwheel turns by their recorded session ID."""
    sessions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trace in traces:
        session_id = trace["meta"].get("session_id")
        if session_id:
            sessions[str(session_id)].append(trace)

    conversations = []
    for group in sessions.values():
        if any(set(trace["models"]) != {observed_model} for trace in group):
            continue
        group.sort(key=lambda trace: (trace["timestamp"], trace["id"]))
        messages = [message for trace in group for message in trace["trace"]]
        user_turns = sum(message.get("role") == "user" for message in messages)
        text = "\n".join(trace["text"] for trace in group if trace["text"])
        if not user_turns or not text.strip():
            continue
        conversations.append(
            {
                "id": group[-1]["id"],
                "text": text,
                "tools": [
                    message["name"]
                    for message in messages
                    if message.get("role") == "tool_call" and message.get("name")
                ],
                "turn_count": user_turns,
            }
        )
    return sorted(conversations, key=lambda conversation: conversation["id"])


def save_history_row(config: dict[str, Any], row: dict[str, Any]) -> None:
    previous = {
        saved["period"]: saved
        for line in HISTORY.read_text().splitlines() if line.strip()
        for saved in [json.loads(line)]
    } if HISTORY.exists() else {}
    previous[row["period"]] = row
    labels = [item["label"] for item in config["periods"]]
    ordered = [previous.pop(label) for label in labels if label in previous]
    ordered.extend(previous.values())
    HISTORY.write_text("".join(json.dumps(item) + "\n" for item in ordered))
    points = [item for item in ordered if item.get("corrected") is not None]
    if len(points) >= 2:
        CHART.write_text(prevalence_chart(
            [
                {
                    "label": item["period"],
                    "corrected": item["corrected"],
                    "ci_low": item["ci_low"],
                    "ci_high": item["ci_high"],
                }
                for item in points
            ],
            threshold=config["threshold"],
            mode=config["judge_mode"],
        ))


def score_saved_period(
    config: dict[str, Any], period: dict[str, str], plan: dict[str, Any], data: dict[str, Any]
) -> dict[str, Any]:
    """Validate saved Part B verdicts, then score and record one period."""
    random_verdicts = data["random_verdicts"]
    risk_verdicts = data["risk_verdicts"]
    random_ids = {trace["id"] for trace in plan["random"]}
    risk_ids = {trace["id"] for group in plan["risk_groups"].values() for trace in group}
    if (
        data["period"] != period["label"]
        or data["judge_id"] != config["judge_id"]
        or data["model"] != config["model"]
        or set(random_verdicts) != random_ids
        or set(risk_verdicts) != risk_ids
        or any(value not in (0, 1) for value in list(random_verdicts.values()) + list(risk_verdicts.values()))
    ):
        raise ValueError("saved verdicts do not match the current period and sample")

    test_labels, test_preds = judge_test_data(config["judge_id"])
    estimate = corrected_mode_prevalence(list(random_verdicts.values()), test_labels, test_preds)
    records = build_score_records(
        config["judge_mode"], random_verdicts, risk_verdicts, estimate, period["label"]
    )
    written = post_scores(records)
    row = {
        "period": period["label"],
        "judge_id": config["judge_id"],
        "model": config["model"],
        "trace_count": data["trace_count"],
        "conversation_count": data["conversation_count"],
        "random_sample_count": len(random_verdicts),
        "risk_sample_count": len(risk_verdicts),
        **estimate,
    }
    save_history_row(config, row)
    print(f"Saved {written} Langfuse scores; raw={estimate['raw']}, corrected={estimate['corrected']}, CI={estimate['ci_low']}-{estimate['ci_high']}")
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    windows = parser.add_mutually_exclusive_group(required=True)
    windows.add_argument("--period", help="period label in monitoring/config.json")
    windows.add_argument("--last-hours", type=int, help="judge eligible sessions in the last N hours")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--judge", action="store_true", help="run the paid frozen judge after reviewing the plan")
    actions.add_argument("--score-saved", action="store_true", help="score saved verdicts without judge calls")
    parser.add_argument("--plan", action="store_true", help="show rolling judge call count without calling the judge")
    parser.add_argument("--as-of", help="fixed UTC end time for a rolling window")
    parser.add_argument("--expected-judge-calls", type=int, help="reject a rolling run if its approved call count changed")
    args = parser.parse_args()

    config = json.loads(CONFIG.read_text())
    if args.last_hours is not None:
        if args.last_hours < 1 or args.judge or args.score_saved:
            parser.error("--last-hours needs a positive number and no period action")
        end = _utc_time(args.as_of) if args.as_of else datetime.now(timezone.utc)
        period = {
            "label": f"daily-{end.strftime('%Y-%m-%dT%H:%M:%SZ')}",
            "from": (end - timedelta(hours=args.last_hours)).isoformat(),
            "to": end.isoformat(),
        }
    else:
        if args.plan or args.as_of or args.expected_judge_calls is not None:
            parser.error("--plan, --as-of, and --expected-judge-calls need --last-hours")
        periods = [period for period in config["periods"] if period["label"] == args.period]
        if len(periods) != 1:
            raise ValueError(f"expected one period labeled {args.period!r}")
        period = periods[0]
    judge = load_monitoring_judge(config["judge_id"])
    if judge["mode"] != config["judge_mode"]:
        raise ValueError("configured judge mode does not match the frozen judge")
    names = config["risk_groups"]
    if not names or len(names) != len(set(names)) or any(name not in DEFAULT_RISK_GROUPS for name in names):
        raise ValueError("configure one or more distinct supported risk groups")

    load_env()
    from langfuse import Langfuse

    output_dir = ROOT / "monitoring" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    status = output_dir / "run-status.json"
    if args.last_hours is not None:
        status.write_text(json.dumps({"period": period["label"], "window_from": period["from"], "window_to": period["to"], "status": "started", "trace_count": 0, "conversation_count": 0}) + "\n")
    if args.last_hours is None:
        scenario_turns = _scenario_turns()
        traces = fetch_period_traces(period, set(scenario_turns), Langfuse())
        conversations = build_conversations(
            traces, scenario_turns, config.get("observed_model", config["model"])
        )
    else:
        traces = fetch_period_traces(period, None, Langfuse())
        conversations = build_session_conversations(
            traces, config.get("observed_model", config["model"])
        )
    plan = select_traces(
        conversations,
        config["random_rate"],
        {name: DEFAULT_RISK_GROUPS[name] for name in names},
    )
    print(
        f"{period['label']}: {len(traces)} traces, {len(conversations)} conversations; "
        f"{len(plan['random'])} random, "
        + ", ".join(f"{name}={len(rows)}" for name, rows in plan["risk_groups"].items())
    )
    print(
        f"Agent runs: 0; judge model: {judge['model']}; "
        f"selected conversations: {len(plan['to_judge'])}; "
        f"judge calls this command: {len(plan['to_judge']) if args.judge or (args.last_hours is not None and not args.plan) else 0}"
    )
    if args.last_hours is not None:
        status.write_text(json.dumps({"period": period["label"], "window_from": period["from"], "window_to": period["to"], "status": "selected", "trace_count": len(traces), "conversation_count": len(conversations), "random_sample_count": len(plan["random"]), "judge_calls": len(plan["to_judge"])}) + "\n")
        if not conversations:
            row = {
                "period": period["label"], "judge_id": config["judge_id"],
                "model": config["model"], "trace_count": len(traces),
                "conversation_count": 0, "random_sample_count": 0,
                "risk_sample_count": 0, "raw": None, "corrected": None,
                "ci_low": None, "ci_high": None,
            }
            save_history_row(config, row)
            status.write_text(json.dumps({**row, "window_from": period["from"], "window_to": period["to"], "status": "no_eligible_conversations", "judge_calls": 0}) + "\n")
            return
        if args.expected_judge_calls is not None and len(plan["to_judge"]) != args.expected_judge_calls:
            raise ValueError("eligible judge-call count changed since approval; run a new plan")
        if args.plan:
            return
    if not args.judge and not args.score_saved:
        if args.last_hours is None:
            return

    output = output_dir / f"{period['label']}.json"
    if args.judge or args.last_hours is not None:
        if judge["model"] == "gpt-4o-mini":
            key = os.environ.get("OPENAI_API_KEY", "")
            if not key or any(character.isspace() for character in key):
                raise ValueError("OPENAI_API_KEY is missing or malformed; fix the environment before judging")
        verdicts = judge_sample(config["judge_id"], plan["to_judge"])
        random_ids = [trace["id"] for trace in plan["random"]]
        risk_ids = list(dict.fromkeys(trace["id"] for group in plan["risk_groups"].values() for trace in group))
        data = {
            "period": period["label"],
            "judge_id": config["judge_id"],
            "model": config["model"],
            "trace_count": len(traces),
            "conversation_count": len(conversations),
            "random_verdicts": {trace_id: verdicts[trace_id] for trace_id in random_ids},
            "risk_verdicts": {trace_id: verdicts[trace_id] for trace_id in risk_ids},
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(data, indent=2) + "\n")
    else:
        data = json.loads(output.read_text())
        if data["trace_count"] != len(traces) or data["conversation_count"] != len(conversations):
            raise ValueError("saved verdict counts do not match the current Langfuse period")
    score_saved_period(config, period, plan, data)
    if args.last_hours is not None:
        status.write_text(json.dumps({"period": period["label"], "window_from": period["from"], "window_to": period["to"], "status": "complete", "trace_count": len(traces), "conversation_count": len(conversations), "random_sample_count": len(plan["random"]), "judge_calls": len(plan["to_judge"])}) + "\n")


if __name__ == "__main__":
    main()
