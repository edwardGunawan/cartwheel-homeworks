# Cartwheel session review

Run from the repository root:

```bash
uv run python -m analysis.review_app.server --refresh
```

Open http://127.0.0.1:8021. Later launches can omit `--refresh` to use the last live cache. Collection membership is restricted to the exact trace IDs in `traces/support_traces.json` (263 traces across 250 sessions in the current export). Refreshing reads only those complete traces from the configured Langfuse project; it preserves review state and replaces the cache only after a successful fetch. Credentials stay in `.env` and are never sent to the browser. The server listens on the local computer only.

## Review workflow

1. Search the conversation queue or filter by role and review status. Each conversation groups `cartwheel.session_id`; every turn retains its Langfuse trace ID. Read the user message, assistant explanations, tool evidence and reply in order. System instructions and complete raw execution records are expandable.
2. Select evidence text to write a free-form margin note. The selection stays highlighted while the note editor is open. Add a trace note for observations that have no text span. Mark the turn reviewed, or explicitly record “No failure observed.” Initial open coding stops at the first failure.
3. After reviewing evidence, create draft failure modes in Taxonomy. Record a definition, requirement references, example and boundary; link supporting annotations. Suggested traces appear under each mode, including accepted suggestions that still need a review status. A suggested trace marked reviewed with a failure has a **Confirm positive** button beside it. You can also select any reviewed trace marked with a failure and click **Confirm positive** to save its ID in `confirmed_positive_trace_ids`. For a close negative, select any reviewed trace, read it, and click **Confirm close negative** to save its ID in `confirmed_close_negative_trace_ids`. Existing `close_negative_trace_ids` are candidates awaiting your review, and appear first in the selector once reviewed. Use **Remove** to undo a confirmation. Mark modes final when ready for structured labeling. These definitions and decisions belong to the student.
4. In Labeling, enter an optional evidence comment and click Present or Absent for each trace and final mode. Blank is unanswered. Changing a mode definition invalidates earlier completion counts until the reviewer makes a fresh decision. Labels remain per trace, not per session.
5. Progress shows reviewed traces, missing final-mode decisions, and pending synchronization. Suggestions can be accepted or rejected there or in the evidence margin. Accepting a suggestion creates an annotation, not a binary judgment.

The sample map uses PCA and eight structural clusters over standardized tool count, step count, word count and retrieval presence. It supports exploration, not prevalence estimation or automatic failure detection. Identical features can overlap. The app does not automatically choose the homework review batches or generate AI suggestions. External review-loop tooling can append suggestions to `analysis/state/suggestions.json`; use unique `id`, `trace_id`, `note`, and optionally `mode`, `quote`, `anchor`, `start` and `end`.

## Saved state

Existing `annotations.json`, `patterns.json` and `suggestions.json` are reused without resetting them. Notes and judgments outside the support collection remain on disk, but are excluded from this interface and its counts. Free-form annotations preserve wrapper metadata. New workflow files under `analysis/state/` are created on the first corresponding action:

- `review_status.json`: explicit reviewed/no-failure status per trace.
- `review_judgments.json`: one current decision per trace/mode, review origin, student acceptance, taxonomy revision, stable score ID and synchronization status.
- `review_suggestion_decisions.json`: explicit accepted/rejected suggestion decisions.
- `review_traces.json`: private raw live cache, ignored by Git.

Binary judgments and matching mode label files are saved locally before a synchronous Langfuse score request. A failed request remains pending and visible; Progress offers retry. Stable score IDs make retries and revisions update the same app-owned score rather than create duplicates. A local browser backup retains operations that could not reach the server; recover them from Progress. Do not clear browser storage before recovery.

The UI polls the review state every 10 seconds when no editor is active. Trace refresh is explicit. No model calls are needed to run the interface.

Run the focused offline checks:

```bash
uv run pytest tests/test_review_app.py tests/test_normalization_metadata.py tests/test_langfuse_export.py
```
