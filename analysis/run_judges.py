"""Homework 5 judge inputs and evaluation steps."""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from analysis.helpers import (
    _state,
    freeze_judge,
    judge_alignment,
    register_judge,
    run_judge,
    split_labels,
)
from analysis.helpers.normalization import _text, normalize_trace


ROOT = Path(__file__).resolve().parents[1]
MODE = "unnecessary_messages_or_details"


def _judge_message(message: dict[str, Any]) -> dict[str, Any]:
    """Keep trace evidence while dropping review and scenario metadata."""
    role = message.get("role")
    if role in {"user", "assistant"}:
        return {"role": role, "text": message.get("text", "")}
    if role == "tool_call":
        return {
            "role": role,
            "name": message.get("name"),
            "arguments": message.get("arguments"),
        }
    if role == "tool_result":
        return {
            "role": role,
            "name": message.get("name"),
            "content": message.get("content"),
        }
    if role == "observation":
        return {"role": role, "name": message.get("label"), "text": message.get("text", "")}
    raise ValueError(f"unexpected trace message role: {role!r}")


def prepare_inputs(
    mode: str = MODE,
    trace_source: str | Path = ROOT / "traces/support_traces.json",
    output_path: str | Path = ROOT / "analysis/state/hw5_trace_inputs.json",
    overwrite: bool = False,
) -> list[dict[str, Any]]:
    """Export one judge input per labeled session, retaining evidence through its target reply.

    For a session with several labeled turns, select the latest Fail turn if
    present, otherwise the latest Pass turn. This preserves a failure that an
    otherwise passing later turn would hide. The selected turn's original ID
    links the input to its existing human label. No human verdict is exported.

    Approved Fail and Pass variant selections come from separate review files.
    Do not regenerate the export after the first prompt run.
    """
    labels_path = ROOT / "analysis/state/hw5_labels" / f"{mode}.jsonl"
    labels = [
        json.loads(line)
        for line in labels_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    label_by_id: dict[str, int] = {}
    for row in labels:
        trace_id = row.get("trace_id")
        if not isinstance(trace_id, str) or not trace_id or trace_id in label_by_id:
            raise ValueError(f"missing or duplicate label trace ID: {trace_id!r}")
        if row.get("label") not in (0, 1):
            raise ValueError(f"trace {trace_id} needs a HW5 Pass=1 or Fail=0 label")
        label_by_id[trace_id] = row["label"]

    source = json.loads(Path(trace_source).read_text(encoding="utf-8"))
    raw_traces = source.get("traces") if isinstance(source, dict) else source
    if not isinstance(raw_traces, list):
        raise ValueError("trace source must be a JSON list or contain a 'traces' list")
    sessions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    found_ids: set[str] = set()
    for raw in raw_traces:
        trace = normalize_trace(raw)
        trace_id = trace["trace_id"]
        if trace_id not in label_by_id:
            continue
        final_reply = _text(trace["output"])
        if not final_reply:
            raise ValueError(f"trace {trace_id} has no recorded assistant reply")
        messages = trace["trace"]
        final_positions = [
            index
            for index, message in enumerate(messages)
            if message.get("role") == "assistant" and message.get("text") == final_reply
        ]
        if final_positions:
            messages.pop(final_positions[-1])
        messages.append({"role": "assistant", "text": final_reply})
        if trace_id in found_ids:
            raise ValueError(f"duplicate source trace ID: {trace_id}")
        found_ids.add(trace_id)
        session_id = trace["meta"].get("session_id")
        if not session_id:
            raise ValueError(f"trace {trace_id} has no session ID for conversation grouping")
        sessions[str(session_id)].append(trace)
    missing = set(label_by_id) - found_ids
    if missing:
        raise ValueError(f"{len(missing)} labeled traces missing from source: {sorted(missing)[:5]}")

    records: list[dict[str, Any]] = []
    scenario_by_trace_id: dict[str, str] = {}
    for turns in sessions.values():
        turns.sort(key=lambda row: (row.get("timestamp") or "", row["trace_id"]))
        failures = [turn for turn in turns if label_by_id[turn["trace_id"]] == 0]
        target = (failures or turns)[-1]
        target_index = turns.index(target)
        messages = [
            _judge_message(message)
            for turn in turns[: target_index + 1]
            for message in turn["trace"]
        ]
        if not any(message["role"] == "user" for message in messages):
            raise ValueError(f"trace {target['trace_id']} has no user request")
        if not messages or messages[-1]["role"] != "assistant":
            raise ValueError(f"trace {target['trace_id']} has no final assistant reply")
        records.append({"trace_id": target["trace_id"], "trace": messages})
        scenario_id = target["meta"].get("scenario_id")
        if not scenario_id:
            raise ValueError(f"trace {target['trace_id']} has no scenario ID for variant review")
        scenario_by_trace_id[target["trace_id"]] = str(scenario_id)

    selected_by_scenario = {
        scenario_by_trace_id[record["trace_id"]]: record for record in records
    }
    exclusions: set[str] = set()
    for class_name, expected_label in (("fail", 0), ("pass", 1)):
        selection_path = ROOT / f"analysis/state/hw5_{class_name}_variant_selections.json"
        if not selection_path.exists():
            continue
        selections = json.loads(selection_path.read_text(encoding="utf-8"))
        if selections.get("mode") != mode:
            raise ValueError("variant selection mode does not match label mode")
        seen: set[str] = set()
        for group in selections[f"approved_{class_name}_variant_groups"]:
            scenarios = [group["keep"], *group["exclude"]]
            if len(scenarios) < 2 or len(set(scenarios)) != len(scenarios):
                raise ValueError("each variant group needs distinct conversations")
            keep_label = (
                0 if class_name == "pass" and group.get("keep_label") == "Fail"
                else expected_label
            )
            for scenario_id in scenarios:
                if scenario_id in seen or scenario_id not in selected_by_scenario:
                    raise ValueError(f"duplicate or missing variant scenario: {scenario_id}")
                seen.add(scenario_id)
                trace_id = selected_by_scenario[scenario_id]["trace_id"]
                required_label = keep_label if scenario_id == group["keep"] else expected_label
                if label_by_id[trace_id] != required_label:
                    raise ValueError(
                        f"variant scenario {scenario_id} has the wrong label"
                    )
            exclusions.update(group["exclude"])
    records = [
        record
        for record in records
        if scenario_by_trace_id[record["trace_id"]] not in exclusions
    ]

    balanced_path = ROOT / "analysis/state/hw5_balanced_selection.json"
    if balanced_path.exists():
        balanced = json.loads(balanced_path.read_text(encoding="utf-8"))
        if balanced.get("mode") != mode:
            raise ValueError("balanced selection mode does not match label mode")
        selected_ids: set[str] = set()
        for class_name, expected_label in (("fail", 0), ("pass", 1)):
            entries = balanced[class_name]
            if len(entries) != 30:
                raise ValueError(f"balanced selection needs 30 {class_name} records")
            for entry in entries:
                trace_id = entry["trace_id"]
                if trace_id in selected_ids or label_by_id.get(trace_id) != expected_label:
                    raise ValueError(f"duplicate or wrongly labeled selection: {trace_id}")
                if scenario_by_trace_id.get(trace_id) != entry["scenario_id"]:
                    raise ValueError(f"selection scenario mismatch: {trace_id}")
                selected_ids.add(trace_id)
        eligible_ids = {record["trace_id"] for record in records}
        if not selected_ids <= eligible_ids:
            raise ValueError("balanced selection contains excluded variant records")
        records = [record for record in records if record["trace_id"] in selected_ids]

    records.sort(key=lambda row: row["trace_id"])
    destination = Path(output_path)
    if destination.exists() and not overwrite:
        raise FileExistsError(f"judge input export already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return records


def split_data(mode: str) -> dict[str, list[str]]:
    """Split this mode's saved judge inputs once into train, dev, and test IDs.

    ``mode`` is the failure-mode ID used by the HW5 label file, currently
    ``unnecessary_messages_or_details``. This function writes splits.json only
    when called; defining it does not split the labels.
    """
    if mode != MODE:
        raise ValueError(f"this judge input export is for {MODE!r}, not {mode!r}")

    input_path = ROOT / "analysis/state/hw5_trace_inputs.json"
    records = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError("HW5 judge inputs must be a nonempty JSON list")
    trace_ids = [record["trace_id"] for record in records]
    if any(not isinstance(trace_id, str) or not trace_id for trace_id in trace_ids):
        raise ValueError("every judge input needs an original trace ID")
    if len(trace_ids) != len(set(trace_ids)):
        raise ValueError("judge inputs contain duplicate trace IDs")

    splits_path = _state.state_path("splits.json")
    existing = (
        json.loads(splits_path.read_text(encoding="utf-8"))
        if splits_path.exists()
        else {}
    )
    if mode in existing:
        raise FileExistsError(f"the split for {mode} already exists; keep it fixed")

    return split_labels(
        mode,
        fractions=(0.20, 0.40, 0.40),
        seed=7,
        min_per_class=10,
        eligible_trace_ids=trace_ids,
    )


def run_development(mode: str, prompt_path: str | Path) -> dict[str, Any]:
    """Register one prompt version, judge its dev split, and save alignment.

    Register each prompt only once. If a batch is interrupted, resume with the
    saved judge ID using run_judge and judge_alignment, not this function.
    """
    if mode != MODE:
        raise ValueError(f"this judge input export is for {MODE!r}, not {mode!r}")
    prompt_file = Path(prompt_path)
    if not prompt_file.is_absolute():
        prompt_file = ROOT / prompt_file
    prompt_text = prompt_file.read_text(encoding="utf-8")
    if not prompt_text.strip():
        raise ValueError("judge prompt is empty")

    input_path = ROOT / "analysis/state/hw5_trace_inputs.json"
    records = json.loads(input_path.read_text(encoding="utf-8"))
    input_ids = [record["trace_id"] for record in records]
    splits = _state.read_json(_state.state_path("splits.json"), default={})
    assignment = splits.get(mode, {})
    dev_ids = assignment.get("dev", [])
    split_ids = [
        trace_id
        for name in ("train", "dev", "test")
        for trace_id in assignment.get(name, [])
    ]
    if (
        not dev_ids
        or len(input_ids) != len(set(input_ids))
        or len(split_ids) != len(set(split_ids))
        or set(split_ids) != set(input_ids)
    ):
        raise ValueError("saved split must be disjoint and match the judge input export")

    from observability.instrument import load_env

    load_env()
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("set OPENAI_API_KEY locally before running the judge")
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["CARTWHEEL_JUDGE_TRACE_SOURCE"] = str(input_path)

    history = _state.read_json(
        _state.state_path("judges", f"_history_{mode}.json"),
        default={"versions": []},
    )
    for version in history["versions"]:
        prior_id = version["judge_id"]
        prior = _state.read_json(_state.state_path("judges", f"{prior_id}.json"), default={})
        if prior.get("prompt_text") == prompt_text and prior.get("model") == "gpt-4o-mini":
            raise FileExistsError(
                f"prompt already registered as {prior_id}; resume that judge ID"
            )

    record = register_judge(
        mode=mode,
        prompt_text=prompt_text,
        judge_model="gpt-4o-mini",
    )
    judge_id = record["judge_id"]
    run_judge(judge_id, split="dev", batch_size=10)
    development = judge_alignment(judge_id, split="dev")
    _state.write_json(ROOT / "analysis/report" / f"dev-{judge_id}.json", development)
    return development


def run_test(judge_id: str) -> dict[str, Any]:
    """Score the selected judge on held-out traces, resuming cached batches if needed."""
    judge = _state.read_json(_state.state_path("judges", f"{judge_id}.json"), default=None)
    if not judge or judge.get("mode") != MODE:
        raise ValueError(f"expected a registered {MODE} judge")

    from observability.instrument import load_env

    load_env()
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("set OPENAI_API_KEY locally before running the judge")
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["CARTWHEEL_JUDGE_TRACE_SOURCE"] = str(ROOT / "analysis/state/hw5_trace_inputs.json")

    if judge.get("status") != "frozen":
        freeze_judge(judge_id)
    run_judge(judge_id, split="test", batch_size=10)
    result = judge_alignment(judge_id, split="test")
    _state.write_json(ROOT / "analysis/report" / f"test-{judge_id}.json", result)
    return result
