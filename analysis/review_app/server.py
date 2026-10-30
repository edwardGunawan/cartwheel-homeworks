"""Session-based HW4 review. Run: uv run python -m analysis.review_app.server --refresh."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from analysis.helpers import langfuse_io
from analysis.helpers.normalization import normalize_trace
from analysis.helpers.selection import _kmeans, _standardize
from analysis.server import _write_json
from observability.instrument import load_env
from scenarios.export_langfuse import _jsonable

HERE = Path(__file__).resolve().parent
STATE = HERE.parent / 'state'
SUPPORT_EXPORT = HERE.parents[1] / 'traces' / 'support_traces.json'
LOCK = threading.RLock()
FILES = {'annotations': 'annotations.json', 'patterns': 'patterns.json',
         'suggestions': 'suggestions.json', 'judgments': 'review_judgments.json',
         'reviewed': 'review_status.json', 'decisions': 'review_suggestion_decisions.json'}


def read(name: str, default: Any) -> Any:
    path = STATE / name
    # Corrupt state must never silently become an empty document on the next save.
    return json.loads(path.read_text()) if path.exists() else default


def items(value: Any, key: str) -> list[dict]:
    if isinstance(value, dict):
        value = value.get(key, [])
    return value if isinstance(value, list) else []


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def modes(value: Any) -> list[dict]:
    source = value.get('modes', value) if isinstance(value, dict) else value
    if isinstance(source, dict):
        return [dict(v, name=k) for k, v in source.items() if isinstance(v, dict)]
    return [dict(v, name=v.get('name') or v.get('id')) for v in source or [] if isinstance(v, dict)]


def attributes(record: dict) -> dict:
    meta = record.get('metadata') or {}
    nested = meta.get('attributes') or {}
    if isinstance(nested, str):
        nested = json.loads(nested)
    return {**nested, **meta}


def text_parts(messages: Any) -> str:
    if not isinstance(messages, list):
        return str(messages or '')
    return '\n'.join(str(p['content']) for m in messages if isinstance(m, dict)
                     for p in m.get('parts', []) if p.get('type') == 'text' and p.get('content'))


def prepare(raw: dict) -> dict:
    """Keep all raw evidence; build only a nonduplicated presentation sequence."""
    trace = normalize_trace(raw)
    trace['raw'] = raw
    trace['steps'] = []
    trace['systems'] = []
    observations = sorted(raw.get('observations') or [], key=lambda o: (o.get('startTime') or '', o['id']))
    tools = [o for o in observations if o.get('type') == 'TOOL']
    used = set()
    for obs in observations:
        if obs.get('type') != 'GENERATION':
            continue
        for message in (obs.get('input') or {}).get('messages', []):
            if message.get('role') == 'system':
                content = text_parts([message])
                if content not in trace['systems']:
                    trace['systems'].append(content)
        for mi, message in enumerate(obs.get('output') or []):
            for pi, part in enumerate(message.get('parts') or []):
                key = f"{obs['id']}:{mi}:{pi}"
                if part.get('type') == 'text':
                    trace['steps'].append({'key': key, 'role': 'assistant', 'text': part.get('content', '')})
                elif part.get('type') == 'tool_call':
                    candidates = [o for o in tools if o['id'] not in used and o.get('name') == part.get('name')
                                  and o.get('input') == part.get('arguments')
                                  and o.get('parentObservationId') == obs.get('parentObservationId')
                                  and (o.get('startTime') or '') >= (obs.get('startTime') or '')]
                    match = candidates[0] if candidates else None
                    if match:
                        used.add(match['id'])
                    trace['steps'].append({'key': key, 'role': 'tool', 'name': part.get('name'),
                        'call_id': part.get('id'), 'arguments': part.get('arguments'),
                        'result': match.get('output') if match else None,
                        'observation_id': match['id'] if match else None,
                        'pairing': 'Matched by function, arguments, parent and time; execution span has no call ID.' if match else 'No matching execution captured.'})
                else:
                    trace['steps'].append({'key': key, 'role': 'observation', 'text': json.dumps(part, indent=2)})
    for tool in tools:
        if tool['id'] not in used:
            trace['steps'].append({'key': tool['id'], 'role': 'tool', 'name': tool.get('name'),
                                  'arguments': tool.get('input'), 'result': tool.get('output'),
                                  'observation_id': tool['id'], 'pairing': 'Unpaired execution; inspect raw timing.'})
    final = text_parts(raw.get('output'))
    if final and not any(s.get('text') == final for s in trace['steps']):
        trace['steps'].append({'key': 'final', 'role': 'assistant', 'text': final})
    trace['user_text'] = text_parts(raw.get('input'))
    trace['tool_count'] = len(tools)
    trace['url'] = os.environ.get('LANGFUSE_HOST', '').rstrip('/') + str(raw.get('htmlPath') or '')
    return trace


def scope_ids() -> set[str]:
    export = json.loads(SUPPORT_EXPORT.read_text())
    records = export['traces'] if isinstance(export, dict) else export
    return {record['id'] for record in records}


def refresh() -> int:
    lf = langfuse_io._client()
    # The export defines membership; Langfuse remains the source of live evidence.
    raw = [_jsonable(lf.api.trace.get(tid)) for tid in sorted(scope_ids())]
    if not raw:
        raise ValueError('The support export is empty; the previous cache was preserved.')
    with LOCK:
        _write_json(STATE / 'review_traces.json', {'fetched_at': now(), 'traces': raw})
    return len(raw)


def revision(mode: dict) -> str:
    rule_fields = ('name', 'definition', 'description', 'requirements', 'spec_refs',
                   'boundary', 'decision_rule', 'include_when', 'exclude_when')
    rule = {key: mode[key] for key in rule_fields if key in mode}
    return hashlib.sha256(json.dumps(rule, sort_keys=True).encode()).hexdigest()[:12]


def state_data() -> dict:
    state = {key: read(file, {} if key in ('patterns', 'reviewed', 'decisions') else []) for key, file in FILES.items()}
    state['annotations'] = items(state['annotations'], 'annotations')
    state['suggestions'] = items(state['suggestions'], 'suggestions')
    state['patterns'] = [{**m, 'revision': revision(m)} for m in modes(state['patterns'])]
    included = scope_ids()
    for key in ('annotations', 'suggestions', 'judgments'):
        state[key] = [entry for entry in state[key] if entry.get('trace_id') in included]
    state['reviewed'] = {tid: value for tid, value in state['reviewed'].items() if tid in included}
    return state


def data() -> dict:
    cache = read('review_traces.json', {'traces': []})
    included = scope_ids()
    traces = [prepare(t) for t in cache['traces'] if t['id'] in included]
    traces.sort(key=lambda t: (t.get('timestamp') or '', t['id']))
    vectors = [[t['tool_count'], len(t['steps']), len(t['text'].split()),
                int(any(s.get('name') in ('search_help_center', 'get_policy') for s in t['steps']))] for t in traces]
    cluster = _kmeans(_standardize(vectors), min(8, len(traces)))
    # PCA uses the project's existing numpy dependency, with no new packages.
    if len(vectors) > 1:
        import numpy as np
        matrix = np.array(_standardize(vectors))
        u, s, _ = np.linalg.svd(matrix, full_matrices=False)
        xy = (u[:, :2] * s[:2]).tolist()
    else:
        xy = [[0, 0] for _ in traces]
    for i, t in enumerate(traces):
        t['cluster'] = cluster[i]
        t['xy'] = xy[i]
    state = state_data()
    return {**state, 'traces': traces, 'fetched_at': cache.get('fetched_at'), 'configured': langfuse_io.is_configured()}


def save_notes(notes: list) -> None:
    raw = read('annotations.json', [])
    if isinstance(raw, dict):
        raw['annotations'] = notes
    else:
        raw = notes
    _write_json(STATE / 'annotations.json', raw)


def save_label(judgment: dict) -> None:
    path = STATE / 'labels' / f"{judgment['mode']}.jsonl"
    labels = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    old = next((label for label in labels if label['trace_id'] == judgment['trace_id']), {})
    label = {**old, 'trace_id': judgment['trace_id'],
             'label_id': old.get('label_id') or f"{judgment['trace_id']}#0",
             'label': judgment['label'], 'source': judgment['source'],
             'ts': judgment['updated_at'], 'note': judgment.get('note') or '',
             'accepted_by': judgment['accepted_by'], 'accepted_at': judgment['accepted_at']}
    if judgment.get('scenario_id'):
        label['scenario_id'] = judgment['scenario_id']
    labels = [label if item['trace_id'] == judgment['trace_id'] else item for item in labels]
    if not old:
        labels.append(label)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.jsonl.tmp')
    tmp.write_text(''.join(json.dumps(item, ensure_ascii=False) + '\n' for item in labels))
    tmp.replace(path)


def sync_judgment(judgment: dict) -> dict:
    judgment['sync'] = 'pending'
    if not langfuse_io.is_configured():
        judgment['sync_error'] = 'Langfuse is not configured. Saved locally; retry when connected.'
        return judgment
    try:
        from langfuse.api.resources.score.types.create_score_request import CreateScoreRequest
        lf = langfuse_io._client()
        metadata = {'source': judgment.get('source', 'human_review').replace('_', '-'),
                    'taxonomy_revision': judgment['taxonomy_revision']}
        if judgment.get('accepted_by'):
            metadata.update(accepted_by=judgment['accepted_by'], accepted_at=judgment['accepted_at'])
        lf.api.score.create(request=CreateScoreRequest(
            id=judgment['score_id'], traceId=judgment['trace_id'], name=judgment['mode'],
            value=judgment['label'], dataType='NUMERIC', comment=judgment.get('note') or '',
            metadata=metadata))
        judgment['sync'] = 'synced'
        judgment.pop('sync_error', None)
    except Exception:
        judgment['sync_error'] = 'Langfuse write failed. Saved locally; retry synchronization.'
    return judgment


def act(payload: dict) -> dict:
    kind = payload.get('kind')
    cache = read('review_traces.json', {'traces': []})
    ids = {t['id'] for t in cache['traces']} & scope_ids()
    tid = payload.get('trace_id')
    if kind not in ('mode', 'suggestion', 'retry') and tid not in ids:
        raise ValueError('Unknown trace ID.')
    if kind == 'note':
        note = str(payload.get('note', '')).strip()
        if not note:
            raise ValueError('Enter a note.')
        notes = items(read('annotations.json', []), 'annotations')
        existing = next((n for n in notes if n.get('id') == payload.get('id')), None)
        if existing and existing.get('trace_id') != tid:
            raise ValueError('Annotation belongs to a different trace.')
        entry = {**(existing or {}), 'id': payload.get('id') or uuid.uuid4().hex,
                 'trace_id': tid, 'note': note, 'quote': payload.get('quote', ''),
                 'anchor': payload.get('anchor', ''), 'start': payload.get('start'),
                 'end': payload.get('end'), 'mode': payload.get('mode', (existing or {}).get('mode', '')),
                 'updated_at': now(), 'source': 'human'}
        notes = [n for n in notes if n.get('id') != entry['id']] + [entry]
        save_notes(notes)
    elif kind == 'delete_note':
        notes = items(read('annotations.json', []), 'annotations')
        save_notes([n for n in notes if not (n.get('id') == payload.get('id') and n.get('trace_id') == tid)])
    elif kind == 'reviewed':
        status = read('review_status.json', {})
        status[tid] = {'reviewed': True, 'outcome': payload.get('outcome'), 'updated_at': now()}
        _write_json(STATE / 'review_status.json', status)
    elif kind == 'mode':
        mode = payload.get('mode') or {}
        name = mode.get('name', '')
        if not re.fullmatch(r'[a-z][a-z0-9_]{1,79}', name) or not str(mode.get('definition', '')).strip():
            raise ValueError('Use a lowercase_mode_name and provide a definition.')
        raw = read('patterns.json', {'modes': []})
        current = modes(raw)
        existing = next((m for m in current if m.get('name') == name), {})
        current = [m for m in current if m.get('name') != name] + [{**existing, **mode, 'updated_at': now()}]
        if isinstance(raw, dict) and 'modes' in raw:
            raw['modes'] = current
        else:
            raw = {m['name']: m for m in current}
        _write_json(STATE / 'patterns.json', raw)
    elif kind in ('positive', 'close_negative'):
        raw = read('patterns.json', {'modes': []})
        current = modes(raw)
        mode = next((m for m in current if m.get('name') == payload.get('mode')), None)
        confirmed = payload.get('confirmed')
        if not mode or type(confirmed) is not bool:
            raise ValueError('Choose a current mode and confirm or remove a trace.')
        status = read('review_status.json', {}).get(tid, {})
        field = 'confirmed_positive_trace_ids' if kind == 'positive' else 'confirmed_close_negative_trace_ids'
        opposite = 'confirmed_close_negative_trace_ids' if kind == 'positive' else 'confirmed_positive_trace_ids'
        if confirmed and kind == 'positive' and status.get('outcome') != 'failure_noted':
            raise ValueError('Mark the trace reviewed with a failure before confirming it as positive.')
        if confirmed and kind == 'close_negative' and not status.get('reviewed'):
            raise ValueError('Review the trace before confirming it as a close negative.')
        if confirmed and tid in (mode.get(opposite) or []):
            raise ValueError('Remove the opposite confirmation for this mode first.')
        existing = mode.get(field) or []
        updated = ([*existing, tid] if tid not in existing else existing) if confirmed else [x for x in existing if x != tid]
        if updated != existing:
            mode[field] = updated
            mode['updated_at'] = now()
            if isinstance(raw, dict) and 'modes' in raw:
                raw['modes'] = current
            else:
                raw = {m['name']: m for m in current}
            _write_json(STATE / 'patterns.json', raw)
    elif kind == 'judgment':
        mode_name = payload.get('mode')
        mode = next((m for m in modes(read('patterns.json', {})) if m['name'] == mode_name), None)
        if not mode or not re.fullmatch(r'[a-z][a-z0-9_]*', mode_name or '') or not mode.get('final', mode.get('status') == 'final') or payload.get('label') not in (0, 1) or type(payload.get('label')) is not int:
            raise ValueError('Choose a current mode and Present or Absent.')
        judgments = read('review_judgments.json', [])
        old = next((j for j in judgments if j['trace_id'] == tid and j['mode'] == mode_name), {})
        mode_revision = revision(mode)
        timestamp = now()
        judgment = {**old, 'trace_id': tid, 'mode': mode_name, 'label': payload['label'],
                    'note': payload.get('note', ''), 'taxonomy_revision': mode_revision,
                    'source': 'human_review', 'accepted_by': 'student', 'accepted_at': timestamp,
                    'updated_at': timestamp, 'sync': 'pending',
                    'score_id': old.get('score_id') or str(uuid.uuid5(uuid.NAMESPACE_URL, f'cartwheel-review:{tid}:{mode_name}'))}
        judgments = [j for j in judgments if not (j['trace_id'] == tid and j['mode'] == mode_name)] + [judgment]
        # Persist before attempting the canonical write; stable score IDs make retries safe.
        _write_json(STATE / 'review_judgments.json', judgments)
        save_label(judgment)
        sync_judgment(judgment)
        _write_json(STATE / 'review_judgments.json', judgments)
    elif kind == 'retry':
        judgments = read('review_judgments.json', [])
        for judgment in judgments:
            if judgment.get('sync') != 'synced':
                sync_judgment(judgment)
        _write_json(STATE / 'review_judgments.json', judgments)
    elif kind == 'suggestion':
        suggestions = items(read('suggestions.json', []), 'suggestions')
        suggestion = next((s for s in suggestions if s.get('id') == payload.get('id')), None)
        if not suggestion or suggestion.get('trace_id') not in ids or payload.get('decision') not in ('accepted', 'rejected'):
            raise ValueError('Unknown suggestion or decision.')
        decisions = read('review_suggestion_decisions.json', {})
        if suggestion['id'] in decisions:
            return {'ok': True}
        if payload['decision'] == 'accepted':
            # Acceptance creates a human note, never an automatic binary verdict.
            act({'kind': 'note', 'id': 'accepted-' + suggestion['id'],
                 'trace_id': suggestion['trace_id'], 'note': suggestion.get('note') or suggestion.get('mode') or 'Accepted suggestion',
                 'quote': suggestion.get('quote', ''), 'anchor': suggestion.get('anchor', ''),
                 'start': suggestion.get('start'), 'end': suggestion.get('end')})
        decisions[suggestion['id']] = {'decision': payload['decision'], 'updated_at': now()}
        _write_json(STATE / 'review_suggestion_decisions.json', decisions)
    else:
        raise ValueError('Unknown action.')
    return {'ok': True}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_: Any) -> None:
        pass

    def reply(self, value: Any, status: int = 200) -> None:
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        try:
            if self.path == '/api/state':
                with LOCK:
                    self.reply(state_data())
            elif self.path == '/api/data':
                with LOCK:
                    self.reply(data())
            elif self.path in ('/', '/app.js', '/style.css'):
                path = HERE / {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}[self.path]
                body = path.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', {'/': 'text/html; charset=utf-8', '/app.js': 'text/javascript; charset=utf-8', '/style.css': 'text/css; charset=utf-8'}[self.path])
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.reply({'error': 'Not found'}, 404)
        except Exception:
            self.reply({'error': 'Unable to read review data. Check local state files.'}, 500)

    def do_POST(self) -> None:
        # Same-origin writes only; do not expose permissive reference-server CORS.
        if not re.fullmatch(r'(127\.0\.0\.1|localhost)(:\d+)?', self.headers.get('Host', '')):
            self.reply({'error': 'Local host required.'}, 403)
            return
        if self.headers.get('Origin') not in (None, f'http://{self.headers.get("Host")}'):
            self.reply({'error': 'Cross-origin write refused.'}, 403)
            return
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            self.reply({'error': 'Expected application/json.'}, 415)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 1_000_000:
                raise ValueError('Invalid request size.')
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError('Expected an object.')
            if self.path == '/api/action':
                with LOCK:
                    self.reply(act(payload))
            elif self.path == '/api/refresh':
                self.reply({'ok': True, 'count': refresh()})
            else:
                self.reply({'error': 'Not found'}, 404)
        except (ValueError, TypeError, KeyError) as exc:
            self.reply({'error': str(exc)}, 400)
        except Exception:
            self.reply({'error': 'Request failed; existing state was preserved. Check Langfuse connectivity or local files.'}, 502)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8021)
    parser.add_argument('--refresh', action='store_true', help='Fetch live traces before serving')
    args = parser.parse_args()
    load_env()
    if args.refresh:
        print(f'Loaded {refresh()} live traces.', flush=True)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Review interface: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
