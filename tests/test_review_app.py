"""Review app checks are offline; Langfuse writes use a fake client."""
import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from analysis.review_app import server


def trace(tid='a' * 32, session='session-one'):
    return {
        'id': tid, 'timestamp': '2026-10-26T01:00:00Z',
        'metadata': {'attributes': {'cartwheel.session_id': session, 'cartwheel.scenario_id': 'same-scenario', 'cartwheel.user_role': 'shopper'}},
        'input': [{'role': 'user', 'parts': [{'type': 'text', 'content': 'Order status?'}]}],
        'output': [{'role': 'assistant', 'parts': [{'type': 'text', 'content': 'Delivered.'}]}],
        'observations': [
            {'id': 'gen', 'parentObservationId': 'agent', 'type': 'GENERATION', 'startTime': '2026-10-26T01:00:00Z',
             'input': {'messages': [{'role': 'system', 'parts': [{'type': 'text', 'content': 'Session context'}]}]},
             'output': [{'role': 'assistant', 'parts': [{'type': 'text', 'content': 'Checking.'}, {'type': 'tool_call', 'name': 'get_order', 'id': 'call-one', 'arguments': {'order_id': 1}}]}]},
            {'id': 'tool', 'parentObservationId': 'agent', 'type': 'TOOL', 'name': 'get_order', 'startTime': '2026-10-26T01:00:01Z', 'input': {'order_id': 1}, 'output': {'ok': True, 'order': {'status': 'delivered'}}},
            {'id': 'last', 'type': 'GENERATION', 'startTime': '2026-10-26T01:00:02Z', 'input': {}, 'output': [{'role': 'assistant', 'parts': [{'type': 'text', 'content': 'Delivered.'}]}]},
        ],
    }


@pytest.fixture
def state(tmp_path, monkeypatch):
    monkeypatch.setattr(server, 'STATE', tmp_path)
    export = tmp_path / 'support_traces.json'
    export.write_text(json.dumps({'traces': [trace(), trace('b' * 32), trace('c' * 32, 'different-session')]}))
    monkeypatch.setattr(server, 'SUPPORT_EXPORT', export)
    monkeypatch.setattr(server.langfuse_io, 'is_configured', lambda: False)
    server._write_json(tmp_path / 'review_traces.json', {'traces': [trace(), trace('b' * 32), trace('c' * 32, 'different-session')]})
    server._write_json(tmp_path / 'annotations.json', {'annotations': [], 'preserve': 'student-work'})
    return tmp_path


def test_evidence_pairing_and_no_duplicate_final(state):
    prepared = server.prepare(trace())
    assert [s['role'] for s in prepared['steps']] == ['assistant', 'tool', 'assistant']
    assert prepared['steps'][1]['call_id'] == 'call-one'
    assert prepared['steps'][1]['observation_id'] == 'tool'
    assert prepared['steps'][1]['result']['ok'] is True
    assert prepared['systems'] == ['Session context']
    raw = trace()
    raw['observations'][1]['input'] = {'order_id': 999}
    assert server.prepare(raw)['steps'][1]['result'] is None


def test_same_scenario_does_not_merge_sessions_or_lose_trace_ids(state):
    data = server.data()
    assert len(data['traces']) == 3
    assert len({t['id'] for t in data['traces']}) == 3
    assert [t['meta']['session_id'] for t in data['traces']].count('session-one') == 2
    assert all(len(t['xy']) == 2 for t in data['traces'])


def test_notes_preserve_state_and_supporting_mode(state):
    server.act({'kind': 'note', 'trace_id': 'a' * 32, 'id': 'n1', 'note': 'First observation', 'anchor': 'user', 'quote': 'Order', 'start': 0, 'end': 5})
    server.act({'kind': 'note', 'trace_id': 'a' * 32, 'id': 'n1', 'note': 'Updated', 'mode': 'policy_claim'})
    saved = json.loads((state / 'annotations.json').read_text())
    assert saved['preserve'] == 'student-work'
    assert len(saved['annotations']) == 1
    assert saved['annotations'][0]['mode'] == 'policy_claim'
    with pytest.raises(ValueError):
        server.act({'kind': 'note', 'trace_id': 'b' * 32, 'id': 'n1', 'note': 'Wrong trace'})


def test_confirm_positive_requires_human_review_and_can_be_undone(state):
    server.act({'kind': 'mode', 'mode': {'name': 'policy_claim', 'definition': 'Missing citation', 'example': 'Saved student example'}})
    payload = {'kind': 'positive', 'trace_id': 'a' * 32, 'mode': 'policy_claim', 'confirmed': True}
    with pytest.raises(ValueError, match='Mark the trace reviewed'):
        server.act(payload)
    server.act({'kind': 'reviewed', 'trace_id': 'a' * 32, 'outcome': 'failure_noted'})
    server.act({'kind': 'reviewed', 'trace_id': 'b' * 32, 'outcome': 'no_failure'})
    with pytest.raises(ValueError, match='Mark the trace reviewed'):
        server.act({**payload, 'trace_id': 'b' * 32})
    with pytest.raises(ValueError, match='current mode'):
        server.act({**payload, 'mode': 'unknown_mode'})
    server.act(payload)
    server.act(payload)
    mode = server.state_data()['patterns'][0]
    assert mode['confirmed_positive_trace_ids'] == ['a' * 32]
    assert mode['example'] == 'Saved student example'
    server.act({**payload, 'confirmed': False})
    assert server.state_data()['patterns'][0]['confirmed_positive_trace_ids'] == []


def test_confirm_close_negative_preserves_candidates_and_requires_review(state):
    server.act({'kind': 'mode', 'mode': {'name': 'policy_claim', 'definition': 'Missing citation',
                                        'close_negative_trace_ids': ['b' * 32]}})
    negative = {'kind': 'close_negative', 'trace_id': 'b' * 32, 'mode': 'policy_claim', 'confirmed': True}
    with pytest.raises(ValueError, match='Review the trace'):
        server.act(negative)
    server.act({'kind': 'reviewed', 'trace_id': 'b' * 32, 'outcome': 'no_failure'})
    server.act(negative)
    server.act(negative)
    mode = server.state_data()['patterns'][0]
    assert mode['close_negative_trace_ids'] == ['b' * 32]
    assert mode['confirmed_close_negative_trace_ids'] == ['b' * 32]
    server.act({'kind': 'reviewed', 'trace_id': 'b' * 32, 'outcome': 'failure_noted'})
    with pytest.raises(ValueError, match='opposite confirmation'):
        server.act({'kind': 'positive', 'trace_id': 'b' * 32, 'mode': 'policy_claim', 'confirmed': True})
    server.act({'kind': 'reviewed', 'trace_id': 'a' * 32, 'outcome': 'failure_noted'})
    server.act({'kind': 'positive', 'trace_id': 'a' * 32, 'mode': 'policy_claim', 'confirmed': True})
    with pytest.raises(ValueError, match='opposite confirmation'):
        server.act({**negative, 'trace_id': 'a' * 32})
    server.act({**negative, 'confirmed': False})
    mode = server.state_data()['patterns'][0]
    assert mode['confirmed_close_negative_trace_ids'] == []
    assert mode['close_negative_trace_ids'] == ['b' * 32]


def test_example_confirmations_do_not_invalidate_structured_labels(state):
    server.act({'kind': 'mode', 'mode': {'name': 'policy_claim', 'definition': 'Missing citation', 'final': True}})
    server.act({'kind': 'judgment', 'trace_id': 'a' * 32, 'mode': 'policy_claim', 'label': 0})
    before = server.state_data()['patterns'][0]['revision']
    server.act({'kind': 'reviewed', 'trace_id': 'b' * 32, 'outcome': 'no_failure'})
    server.act({'kind': 'close_negative', 'trace_id': 'b' * 32, 'mode': 'policy_claim', 'confirmed': True})
    after = server.state_data()['patterns'][0]['revision']
    assert after == before == server.state_data()['judgments'][0]['taxonomy_revision']


def test_judgment_retries_use_same_score_id_and_revisions(state, monkeypatch):
    server.act({'kind': 'mode', 'mode': {'name': 'policy_claim', 'definition': 'Missing citation', 'final': True}})
    payload = {'kind': 'judgment', 'trace_id': 'a' * 32, 'mode': 'policy_claim', 'label': 1}
    server.act(payload)
    first = server.state_data()['judgments'][0]
    assert first['sync'] == 'pending'
    assert server.state_data()['patterns'][0]['revision'] == first['taxonomy_revision']
    label_path = state / 'labels' / 'policy_claim.jsonl'
    assert json.loads(label_path.read_text())['label'] == 1
    calls = []
    monkeypatch.setattr(server.langfuse_io, 'is_configured', lambda: True)
    monkeypatch.setattr(server.langfuse_io, '_client', lambda: SimpleNamespace(api=SimpleNamespace(score=SimpleNamespace(create=lambda **kwargs: calls.append(kwargs['request'])))))
    server.act({'kind': 'retry'})
    payload['label'] = 0
    server.act(payload)
    saved = server.state_data()['judgments']
    assert len(saved) == 1 and saved[0]['sync'] == 'synced' and saved[0]['label'] == 0
    assert calls[0].id == calls[1].id == first['score_id']
    assert calls[0].trace_id == 'a' * 32
    label = json.loads(label_path.read_text())
    assert label['label'] == 0 and label['source'] == 'human_review'
    assert label['accepted_at'] == saved[0]['accepted_at']
    assert calls[-1].metadata['accepted_by'] == 'student'
    assert calls[-1].metadata['source'] == 'human-review'
    server.act({'kind': 'mode', 'mode': {'name': 'policy_claim', 'definition': 'Revised definition', 'final': True}})
    assert server.state_data()['patterns'][0]['revision'] != saved[0]['taxonomy_revision']
    with pytest.raises(ValueError):
        server.act({**payload, 'label': True})


def test_retry_preserves_accepted_agent_review_origin(state, monkeypatch):
    judgment = {'trace_id': 'a' * 32, 'mode': 'policy_claim', 'label': 1,
                'score_id': 'score-one', 'taxonomy_revision': 'revision-one',
                'source': 'agent_review', 'accepted_by': 'student',
                'accepted_at': '2026-10-30T00:00:00+00:00', 'sync': 'pending'}
    server._write_json(state / 'review_judgments.json', [judgment])
    calls = []
    monkeypatch.setattr(server.langfuse_io, 'is_configured', lambda: True)
    monkeypatch.setattr(server.langfuse_io, '_client', lambda: SimpleNamespace(api=SimpleNamespace(score=SimpleNamespace(create=lambda **kwargs: calls.append(kwargs['request'])))))
    server.act({'kind': 'retry'})
    assert calls[0].metadata['source'] == 'agent-review'
    assert calls[0].metadata['accepted_at'] == judgment['accepted_at']


def test_acceptance_does_not_create_binary_judgment(state):
    server._write_json(state / 'suggestions.json', [{'id': 's1', 'trace_id': 'a' * 32, 'note': 'Possible problem', 'quote': 'Order'}])
    server.act({'kind': 'suggestion', 'id': 's1', 'decision': 'accepted'})
    server.act({'kind': 'suggestion', 'id': 's1', 'decision': 'accepted'})
    data = server.state_data()
    assert len(data['annotations']) == 1
    assert data['judgments'] == []
    assert data['decisions']['s1']['decision'] == 'accepted'


def test_corrupt_state_is_not_silently_overwritten(state):
    (state / 'annotations.json').write_text('{broken')
    with pytest.raises(json.JSONDecodeError):
        server.act({'kind': 'note', 'trace_id': 'a' * 32, 'note': 'New note'})
    assert (state / 'annotations.json').read_text() == '{broken'


def test_http_routes_and_cross_origin_writes(state):
    import threading
    from http.server import ThreadingHTTPServer
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen

    http = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{http.server_port}'
    try:
        with urlopen(base + '/api/data') as response:
            assert len(json.load(response)['traces']) == 3
        with urlopen(base + '/api/state') as response:
            assert json.load(response)['annotations'] == []
        req = Request(base + '/api/action', data=json.dumps({'kind': 'reviewed', 'trace_id': 'a' * 32, 'outcome': 'no_failure'}).encode(), headers={'Content-Type': 'application/json', 'Origin': base})
        with urlopen(req) as response:
            assert json.load(response)['ok']
        req.add_header('Origin', 'https://unrelated.example')
        with pytest.raises(HTTPError) as error:
            urlopen(req)
        assert error.value.code == 403
        with urlopen(base + '/app.js') as response:
            assert b'renderReview' in response.read()
    finally:
        http.shutdown()
        http.server_close()
        thread.join()


def test_collection_scope_preserves_all_saved_annotations(state, monkeypatch):
    server.act({'kind': 'note', 'trace_id': 'a' * 32, 'id': 'kept', 'note': 'Existing support note'})
    notes = json.loads((state / 'annotations.json').read_text())
    notes['annotations'].append({'id': 'outside', 'trace_id': 'd' * 32, 'note': 'Earlier pilot note'})
    server._write_json(state / 'annotations.json', notes)
    before = (state / 'annotations.json').read_bytes()
    cache = json.loads((state / 'review_traces.json').read_text())
    cache['traces'].append(trace('d' * 32, 'pilot-session'))
    server._write_json(state / 'review_traces.json', cache)
    result = server.data()
    assert {t['id'] for t in result['traces']} == {'a' * 32, 'b' * 32, 'c' * 32}
    assert [n['id'] for n in result['annotations']] == ['kept']
    assert (state / 'annotations.json').read_bytes() == before
    with pytest.raises(ValueError):
        server.act({'kind': 'note', 'trace_id': 'd' * 32, 'note': 'Outside collection'})


def test_refresh_fetches_only_export_ids_and_preserves_notes(state, monkeypatch):
    calls = []
    def get(tid):
        calls.append(tid)
        return trace(tid)
    monkeypatch.setattr(server.langfuse_io, '_client', lambda: SimpleNamespace(api=SimpleNamespace(trace=SimpleNamespace(get=get))))
    before = (state / 'annotations.json').read_bytes()
    assert server.refresh() == 3
    assert set(calls) == server.scope_ids()
    assert (state / 'annotations.json').read_bytes() == before
