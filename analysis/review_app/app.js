'use strict';
const $ = s => document.querySelector(s);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pretty = value => JSON.stringify(value, null, 2);
let state, sessions = [], current, view = 'review', pendingNote, busy = false, lastState = '', requestQueue = Promise.resolve();
const palette = ['#245d4f','#67599a','#b67b36','#537b9c','#ac596d','#778744','#977058','#3a8589'];
const finalModes = () => state.patterns.filter(m => m.final === true || (m.final === undefined && m.status === 'final'));
const judgment = (tid, mode) => state.judgments.find(j => j.trace_id === tid && j.mode === mode.name);
const complete = (tid, mode) => { const j = judgment(tid, mode); return j && j.taxonomy_revision === mode.revision; };
const reviewed = tid => state.reviewed[tid]?.reviewed;
const pendingSuggestions = () => state.suggestions.filter(s => !state.decisions[s.id] && state.traces.some(t => t.id === s.trace_id));
function notify(message) { $('#notice').textContent = message; $('#notice').hidden = false; clearTimeout(notify.timer); notify.timer = setTimeout(() => $('#notice').hidden = true, 7000); }
async function api(path, payload) {
  const response = await fetch(path, payload === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Unable to save.');
  return result;
}
function syncStatus() {
  const pending = state.judgments.filter(j => j.sync !== 'synced').length;
  $('#save-status').textContent = busy ? 'Saving…' : pending ? `Saved locally · ${pending} awaiting Langfuse` : 'Saved locally' + (state.judgments.length ? ' · Langfuse synced' : '');
  $('#save-status').className = pending ? 'error' : '';
}
async function updateState() {
  const next = await api('/api/state');
  Object.assign(state, next); lastState = JSON.stringify(next); syncStatus(); renderQueue();
}
function action(payload, rerender = true) {
  if(payload.kind === 'note' && !payload.id) payload.id = crypto.randomUUID();
  const run = async () => {
    busy = true; syncStatus();
    const backup = JSON.parse(localStorage.getItem('cartwheel-review-pending') || '{}');
    const operation = crypto.randomUUID(); backup[operation] = payload;
    localStorage.setItem('cartwheel-review-pending', JSON.stringify(backup));
    try {
      await api('/api/action', payload);
      delete backup[operation]; localStorage.setItem('cartwheel-review-pending', JSON.stringify(backup));
      await updateState();
      if (rerender) render();
    } catch (error) { notify(`${error.message} Your change is backed up in this browser. Use “Recover browser changes” in Progress.`); throw error; }
    finally { busy = false; syncStatus(); }
  };
  const result = requestQueue.then(run, run); requestQueue = result.catch(() => {}); return result;
}
function groupSessions() {
  const groups = new Map();
  for (const t of state.traces) {
    const sid = t.meta.session_id || t.id;
    if (!groups.has(sid)) groups.set(sid, {id:sid, traces:[]});
    groups.get(sid).traces.push(t);
  }
  sessions = [...groups.values()];
  if (!sessions.some(s => s.id === current)) current = sessions[0]?.id;
}
function filteredSessions() {
  const query = $('#search').value.toLowerCase(), role = $('#role').value, status = $('#filter').value;
  return sessions.filter(s => (!role || s.traces[0].meta.role === role) &&
    (!status || s.traces.some(t => status === 'reviewed' ? reviewed(t.id) : !reviewed(t.id))) &&
    (!query || s.traces.some(t => `${t.id} ${t.meta.scenario_id} ${t.meta.session_id} ${t.text}`.toLowerCase().includes(query))));
}
function renderQueue() {
  const shown = filteredSessions();
  $('#queue-count').textContent = `${sessions.length} sessions · ${state.traces.length} traces`;
  $('#session-list').innerHTML = shown.map(s => {
    const t = s.traces[0], n = s.traces.filter(t => reviewed(t.id)).length;
    return `<button class="session ${current === s.id ? 'active' : ''}" data-session="${esc(s.id)}"><strong>${esc(t.meta.scenario_id || s.id.slice(0,12))} · ${esc(t.meta.role)}</strong><span class="preview">${esc(t.user_text)}</span><small>${s.traces.length} turn${s.traces.length === 1 ? '' : 's'} · ${n}/${s.traces.length} reviewed</small></button>`;
  }).join('') || '<p class="muted">No matching conversations.</p>';
  $('#fetched').textContent = state.fetched_at ? `Live trace cache · ${new Date(state.fetched_at).toLocaleString()}` : 'No traces loaded. Refresh from Langfuse.';
}
function head(title, subtitle, actionHTML = '') { return `<div class="page-head"><div><div class="eyebrow">Human error discovery</div><h1>${title}</h1><div class="meta">${subtitle}</div></div>${actionHTML}</div>`; }
function annotatable(tid, key, text, tag = 'div') { return `<${tag} class="annotatable" data-tid="${esc(tid)}" data-anchor="${esc(key)}">${tag === 'pre' ? esc(text) : esc(text).replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/`([^`]+)`/g,'<code>$1</code>')}</${tag}>`; }
function resultHTML(t, step) {
  const result = step.result;
  if (result == null) return '<p class="muted">No tool result captured. See execution details.</p>';
  const key = step.key + ':result';
  let rich = '';
  if (Array.isArray(result.orders) || result.order) {
    const rows = result.orders || [result.order];
    const columns = ['order_id','store_id','store_name','product_id','status','total_usd','ordered_at','shipped_at','delivered_at','refund_eligible'].filter(c => rows.some(r => Object.hasOwn(r,c)));
    rich = `<div class="table-wrap annotatable" data-tid="${esc(t.id)}" data-anchor="${esc(key + ':table')}"><table><thead><tr>${columns.map(c => `<th>${esc(c.replaceAll('_',' '))}</th>`).join('')}</tr></thead><tbody>${rows.map(r => `<tr>${columns.map(c => `<td>${esc(r[c] === null ? 'null' : r[c])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  } else if (Array.isArray(result.results)) {
    rich = result.results.map((r,i) => `<article class="retrieval"><div class="meta">Rank ${i+1} · ${esc(r.policy_id)} · retrieval score ${esc(r.score)}</div><strong>${esc(r.title)}</strong>${annotatable(t.id, key + ':snippet:' + i, r.snippet)}</article>`).join('');
  } else if (result.body) {
    rich = `<div class="meta">Full policy · ${esc(result.policy_id)} · ${esc(result.audience)}</div><h3>${esc(result.title)}</h3>${annotatable(t.id, key + ':body', result.body)}`;
  }
  const summary = result.ok === false ? `${result.error}: ${result.reason}` : result.status || (result.orders ? `${result.orders.length} orders returned` : result.results ? `${result.results.length} policy matches` : result.order ? `Order ${result.order.order_id}: ${result.order.status}` : result.policy_id || 'Tool result');
  const raw = annotatable(t.id, key + ':json', pretty(result), 'pre');
  return `<div class="meta">${esc(result.ok === false ? 'ok: false' : result.ok === true ? 'ok: true' : 'Status not supplied')} · ${esc(summary)}</div>${rich}${rich ? `<details class="raw"><summary>Complete result JSON</summary>${raw}</details>` : raw}`;
}
function stepHTML(t, s) {
  if (s.role !== 'tool') return `<section class="message ${esc(s.role)}"><div class="role">${esc(s.role)}</div>${annotatable(t.id,s.key,s.text)}</section>`;
  return `<section class="tool-step"><div class="tool-head"><span class="role">Tool call → result</span><br><strong>${esc(s.name)}()</strong><div class="meta">${esc(s.call_id || s.observation_id)}</div></div><details class="tool-part"><summary>Arguments</summary>${annotatable(t.id,s.key + ':args',pretty(s.arguments),'pre')}</details><div class="tool-part">${resultHTML(t,s)}</div><details class="tool-part"><summary>Call/result matching</summary><p class="muted">${esc(s.pairing)}</p></details></section>`;
}
function renderReview() {
  const session = sessions.find(s => s.id === current);
  if (!session) return head('Your review collection', 'Refresh from Langfuse to begin.');
  const first = session.traces[0], meta = first.meta;
  return head(esc(meta.scenario_id || 'Conversation'), `${esc(meta.role)} · ${session.traces.length} trace${session.traces.length === 1 ? '' : 's'} · session ${esc(session.id.slice(0,12))}`, '<button id="next-session">Next conversation →</button>') +
    `<div class="session-context">Read the conversation in order. Write a free-form note at the first failure, then stop the initial review of that trace. Use Labeling later to record every final mode.</div>` + session.traces.map((t,i) => {
      const status = state.reviewed[t.id];
      return `<article class="trace" id="trace-${esc(t.id)}"><div class="trace-title"><div><strong>Turn ${i+1}</strong> <span class="pill">${status?.reviewed ? esc(status.outcome === 'no_failure' ? 'No failure observed' : 'Reviewed') : 'Not reviewed'}</span><div class="meta"><span>${esc(t.id)}</span><span>${new Date(t.timestamp).toLocaleString()}</span>${/^https?:\/\//.test(t.url) ? `<a href="${esc(t.url)}" target="_blank" rel="noopener">Open in Langfuse ↗</a>` : ''}</div></div><div class="meta">${t.tool_count} tool calls · ${esc(t.models.join(', '))}</div></div><div class="evidence-layout"><div class="transcript">${t.systems.map((s,n) => `<details class="message system"><summary>System instructions${t.systems.length > 1 ? ' · version ' + (n+1) : ''}</summary><div class="role">System · fully captured</div>${annotatable(t.id,'system:' + n,s)}</details>`).join('')}<section class="message user"><div class="role">User</div>${annotatable(t.id,'user',t.user_text)}</section>${t.steps.map(s => stepHTML(t,s)).join('')}${!t.steps.some(s => s.role === 'assistant') ? '<div class="session-context">No assistant text was captured in this trace. Inspect the complete execution record for available evidence.</div>' : ''}<div class="trace-actions"><button data-add-note="${esc(t.id)}">Add trace note</button><button data-reviewed="${esc(t.id)}" data-outcome="failure_noted">Mark reviewed</button><button data-reviewed="${esc(t.id)}" data-outcome="no_failure">No failure observed</button></div><details class="raw"><summary>Complete execution record · prompts, timing, usage and metadata</summary><pre>${esc(pretty(t.raw))}</pre></details></div><div class="notes" data-notes="${esc(t.id)}"></div></div></article>`;
    }).join('');
}
function renderTaxonomy() {
  const notes = state.annotations;
  return head('Failure taxonomy', 'Definitions, boundaries and the human evidence behind them.', '<button id="new-mode" class="primary">Add failure mode</button>') +
  (state.patterns.length ? `<div class="mode-grid">${state.patterns.map(m => {
    const support = notes.filter(n => n.mode === m.name || (m.annotation_ids || []).includes(n.id));
    const confirmed = m.confirmed_positive_trace_ids || [];
    const confirmedNegatives = m.confirmed_close_negative_trace_ids || [];
    const candidates = m.close_negative_trace_ids || [];
    const suggested = state.suggestions.filter(s => s.mode === m.name && state.decisions[s.id]?.decision !== 'rejected' && !confirmed.includes(s.trace_id) && state.traces.some(t => t.id === s.trace_id));
    const suggestedIds = suggested.map(s => s.trace_id);
    const choices = state.traces.filter(t => state.reviewed[t.id]?.outcome === 'failure_noted' && !confirmed.includes(t.id) && !confirmedNegatives.includes(t.id)).sort((a,b) => Number(suggestedIds.includes(b.id)) - Number(suggestedIds.includes(a.id)));
    const negativeChoices = state.traces.filter(t => reviewed(t.id) && !confirmed.includes(t.id) && !confirmedNegatives.includes(t.id)).sort((a,b) => Number(candidates.includes(b.id)) - Number(candidates.includes(a.id)));
    return `<section class="panel mode-card" style="flex-grow:${Math.max(1,support.length)}">
      <h2>${esc(m.name)}</h2><span class="pill">${m.final === true || (m.final === undefined && m.status === 'final') ? 'Final' : 'Draft'}</span><span class="pill">${support.length} supporting notes</span>
      <p>${esc(m.definition || m.description)}</p><p class="muted">Requirements: ${esc(m.requirements || m.spec_refs || 'Not recorded')}</p>
      <blockquote>${esc(m.example || 'No positive example recorded.')}</blockquote><p class="muted">Boundary: ${esc(m.boundary || 'Not recorded')}</p>
      <button data-edit-mode="${esc(m.name)}">Edit definition</button>
      <h3>Confirmed positive traces (${confirmed.length})</h3>
      ${confirmed.map(tid => { const t = state.traces.find(t => t.id === tid); return `<div class="trace-actions"><button data-jump="${esc(tid)}">${esc(t?.meta.scenario_id || tid)} · ${esc(tid.slice(0,8))}</button><button data-positive-remove="${esc(tid)}" data-mode="${esc(m.name)}">Remove</button></div>`; }).join('') || '<p class="muted">No confirmed positive traces yet.</p>'}
      <label>Reviewed trace with failure noted<select data-positive-select="${esc(m.name)}"><option value="">Select a trace</option>${choices.map(t => `<option value="${esc(t.id)}">${suggestedIds.includes(t.id) ? 'Suggested · ' : ''}${esc(t.meta.scenario_id)} · ${esc(t.id)}</option>`).join('')}</select></label>
      <button data-positive-open="${esc(m.name)}">Read selected</button> <button data-positive-add="${esc(m.name)}">Confirm positive</button>
      ${suggested.length ? `<h3>Suggested traces to review</h3>${suggested.map(s => { const t = state.traces.find(t => t.id === s.trace_id); const outcome = state.reviewed[s.trace_id]?.outcome; const status = outcome === 'failure_noted' ? 'Reviewed with failure' : outcome === 'no_failure' ? 'Reviewed: no failure observed' : 'Read and mark reviewed with a failure to confirm'; return `<div class="trace-actions"><button data-jump="${esc(s.trace_id)}">${esc(t?.meta.scenario_id || s.trace_id)} · ${esc(s.trace_id.slice(0,8))}</button><span class="muted">${state.decisions[s.id]?.decision === 'accepted' ? 'Suggestion accepted · ' : 'AI suggestion · '}${status}</span>${outcome === 'failure_noted' && !confirmedNegatives.includes(s.trace_id) ? `<button data-positive-add="${esc(m.name)}" data-trace-id="${esc(s.trace_id)}">Confirm positive</button>` : ''}</div>`; }).join('')}` : ''}
      <h3>Confirmed close negatives (${confirmedNegatives.length})</h3>
      <p class="muted">Similar traces that do not meet this mode's definition. Existing candidate IDs are suggestions, not confirmations.</p>
      ${confirmedNegatives.map(tid => { const t = state.traces.find(t => t.id === tid); return `<div class="trace-actions"><button data-jump="${esc(tid)}">${esc(t?.meta.scenario_id || tid)} · ${esc(tid.slice(0,8))}</button><button data-negative-remove="${esc(tid)}" data-mode="${esc(m.name)}">Remove</button></div>`; }).join('') || '<p class="muted">No confirmed close negatives yet.</p>'}
      <label>Reviewed trace<select data-negative-select="${esc(m.name)}"><option value="">Select a trace</option>${negativeChoices.map(t => `<option value="${esc(t.id)}">${candidates.includes(t.id) ? 'Candidate · ' : ''}${esc(t.meta.scenario_id)} · ${esc(t.id)}</option>`).join('')}</select></label>
      <button data-negative-open="${esc(m.name)}">Read selected</button> <button data-negative-add="${esc(m.name)}">Confirm close negative</button>
      ${candidates.filter(tid => !reviewed(tid)).map(tid => `<div class="trace-actions"><button data-jump="${esc(tid)}">Read candidate · ${esc(tid.slice(0,8))}</button><span class="muted">Review before confirming</span></div>`).join('')}
      ${support.map(n => `<button class="support" data-jump="${esc(n.trace_id)}" data-note-jump="${esc(n.id)}">${esc(n.note)}</button>`).join('')}
    </section>`;
  }).join('')}</div>` : '<div class="panel">No modes defined yet. Begin with free-form observations; create categories after reviewing evidence.</div>') +
  `<section class="panel"><h2>Link supporting annotations</h2><p class="muted">Link existing notes after open coding. This does not create a binary judgment.</p>${notes.length ? notes.map(n => `<div class="support-row"><button data-jump="${esc(n.trace_id)}" data-note-jump="${esc(n.id)}">${esc(n.trace_id.slice(0,8))}</button> ${esc(n.note)} <label>Supporting mode<select data-link-note="${esc(n.id)}"><option value="">Unassigned</option>${state.patterns.map(m => `<option value="${esc(m.name)}" ${n.mode === m.name ? 'selected' : ''}>${esc(m.name)}</option>`).join('')}</select></label></div>`).join('') : '<p class="muted">Your annotations will appear here.</p>'}</section>`;
}
function renderLabels() {
  const modes = finalModes(), visible = filteredSessions().flatMap(s => s.traces);
  return head('Structured labeling', 'One explicit decision per trace and final mode. 1 = present · 0 = absent. Blank means unanswered.') +
  (!modes.length ? '<div class="panel">Finalize a mode in Taxonomy to begin labeling.</div>' : `<div class="panel table-wrap" style="max-height:none"><table><thead><tr><th>Trace / conversation</th>${modes.map(m => `<th title="${esc(m.definition)}">${esc(m.name)}</th>`).join('')}</tr></thead><tbody>${visible.map(t => `<tr><td><button data-jump="${esc(t.id)}">${esc(t.meta.scenario_id)} · ${esc(t.id.slice(0,8))}</button><p class="muted">${esc(t.user_text.slice(0,110))}</p></td>${modes.map(m => {
    const j = judgment(t.id,m), valid = complete(t.id,m);
    return `<td class="judgment-cell"><div><button data-label="1" data-tid="${esc(t.id)}" data-mode="${esc(m.name)}" aria-pressed="${!!valid && j.label === 1}">Present</button> <button data-label="0" data-tid="${esc(t.id)}" data-mode="${esc(m.name)}" aria-pressed="${!!valid && j.label === 0}">Absent</button></div><span class="muted">${!j ? 'Unanswered' : !valid ? 'Definition changed — re-review' : j.sync === 'synced' ? 'Saved · synced' : 'Saved locally · sync pending'}</span><label>Evidence / comment<input class="judgment-note" data-comment="${esc(t.id + ':' + m.name)}" value="${esc(j?.note || '')}" placeholder="Saved with your decision"></label></td>`;
  }).join('')}</tr>`).join('')}</tbody></table></div>`);
}
function renderProgress() {
  const modes = finalModes(), n = state.traces.length, done = state.traces.filter(t => reviewed(t.id)).length;
  const missing = state.traces.flatMap(t => modes.filter(m => !complete(t.id,m)).map(m => ({t,m})));
  const valid = n*modes.length - missing.length, suggestions = pendingSuggestions();
  return head('Review progress', 'Counts use distinct trace IDs, even when conversations contain several turns.') +
  `<div class="cards"><div class="stat"><strong>${done} / ${n}</strong><small>Traces reviewed</small><div class="bar"><span style="width:${n ? 100*done/n : 0}%"></span></div></div><div class="stat"><strong>${valid} / ${n*modes.length}</strong><small>Current final-mode decisions</small></div><div class="stat"><strong>${state.judgments.filter(j => j.sync !== 'synced').length}</strong><small>Judgments awaiting Langfuse</small></div><div class="stat"><strong>${suggestions.length}</strong><small>AI suggestions awaiting you</small></div></div><section class="panel"><h2>Save & synchronization</h2><p class="muted">Free-form notes are saved locally. Accepted binary judgments are mirrored in review_judgments.json and sent to Langfuse with stable score IDs. Revised definitions require new human decisions.</p><button id="retry-sync">Retry Langfuse synchronization</button> <button id="recover">Recover browser changes</button><p class="muted">${state.configured ? 'Langfuse credentials are configured.' : 'Langfuse is not configured; judgments remain pending locally.'}</p></section>` +
  `<section class="panel"><h2>AI suggestions</h2><p class="muted">Accepting a suggestion creates a human annotation. Binary labels always require a separate explicit decision.</p>${suggestions.length ? '<label class="check"><input id="select-suggestions" type="checkbox"> Select all suggestions</label><button id="accept-selected">Accept selected</button> <button id="reject-selected">Reject selected</button>' : ''}${suggestions.map(s => `<article class="retrieval"><label class="check"><input type="checkbox" data-suggestion-select="${esc(s.id)}"> Include suggestion</label><span class="pill">AI suggestion</span> <strong>${esc(s.mode || 'Observation')}</strong><blockquote>${esc(s.quote)}</blockquote><p>${esc(s.note)}</p><button data-jump="${esc(s.trace_id)}">Read evidence</button> <button data-suggestion="${esc(s.id)}" data-decision="accepted">Accept</button> <button data-suggestion="${esc(s.id)}" data-decision="rejected">Reject</button></article>`).join('') || '<p class="muted">No pending suggestions. No AI review has been run.</p>'}</section>` +
  `<section class="panel"><h2>Incomplete judgments (${missing.length})</h2>${missing.slice(0,60).map(({t,m}) => `<p><button data-jump="${esc(t.id)}">${esc(t.meta.scenario_id)} · ${esc(t.id.slice(0,8))}</button> <span class="muted">${esc(m.name)}</span></p>`).join('') || '<p class="muted">No incomplete judgments for current final modes.</p>'}${missing.length > 60 ? '<p class="muted">First 60 shown. Use Labeling to see all.</p>' : ''}</section>`;
}
function renderMap() {
  const traces = filteredSessions().flatMap(s => s.traces), all = state.traces;
  const xs = all.map(t=>t.xy[0]), ys = all.map(t=>t.xy[1]);
  const minX = Math.min(...xs), minY = Math.min(...ys), spanX = Math.max(...xs)-minX || 1, spanY = Math.max(...ys)-minY || 1;
  const coord = t => [40+920*(t.xy[0]-minX)/spanX, 40+430*(t.xy[1]-minY)/spanY];
  return head('Explore the trace collection', 'PCA projection of standardized tool count, step count, word count and retrieval presence. Nearby points have similar structure.') +
  `<p class="muted">${traces.length} traces match the queue filters. Color = structural cluster; outline = reviewed. Click a point to read its session. This map does not measure quality or failure prevalence.</p><svg id="map-svg" viewBox="0 0 1000 510" role="img" aria-label="Structural trace map">${traces.map(t => { const [x,y]=coord(t); return `<circle cx="${x}" cy="${y}" r="${reviewed(t.id) ? 7 : 5}" fill="${palette[t.cluster % palette.length]}" stroke="${reviewed(t.id) ? '#182c29' : 'white'}" stroke-width="${reviewed(t.id) ? 3 : 1}" tabindex="0" role="button" aria-label="Open ${esc(t.meta.scenario_id)} ${esc(t.id.slice(0,8))}" data-jump="${esc(t.id)}"><title>${esc(t.meta.scenario_id)} · ${esc(t.meta.role)} · ${t.tool_count} tools · ${state.annotations.filter(n=>n.trace_id===t.id).length} notes · ${reviewed(t.id) ? 'reviewed' : 'unreviewed'}</title></circle>`; }).join('')}</svg><div class="legend">${[...new Set(all.map(t=>t.cluster))].sort().map(c=>`<span><i style="background:${palette[c % palette.length]}"></i>Cluster ${c+1}</span>`).join('')}</div><p class="muted">Projection can overlap traces with identical features. Use the searchable queue to access each trace individually.</p>`;
}
function render() {
  if (!state) return;
  document.querySelectorAll('nav button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));
  $('#main').innerHTML = ({review:renderReview,taxonomy:renderTaxonomy,labels:renderLabels,map:renderMap,progress:renderProgress})[view]();
  if (view === 'review') { renderNotes(); requestAnimationFrame(layoutNotes); }
}
function jump(tid, noteID) {
  const session = sessions.find(s=>s.traces.some(t=>t.id===tid));
  if (!session) return notify('This annotation refers to a trace outside the loaded collection.');
  current=session.id; view='review'; renderQueue(); render();
  requestAnimationFrame(()=>{
    const note = noteID && [...document.querySelectorAll('[data-note-id]')].find(n=>n.dataset.noteId===noteID);
    const mark = noteID && [...document.querySelectorAll('mark[data-note-id]')].find(n=>n.dataset.noteId===noteID);
    if(mark){let parent=mark.parentElement;while(parent){if(parent.tagName==='DETAILS')parent.open=true;parent=parent.parentElement;}layoutNotes();}
    const target = mark || note || document.getElementById('trace-'+tid);
    target?.scrollIntoView({block:'start',behavior:'smooth'});
  });
}
function highlight(el, start, end, id, cls='') {
  const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT), nodes=[]; let node, offset=0;
  while ((node=walker.nextNode())) { const a=Math.max(0,start-offset), b=Math.min(node.length,end-offset); if(b>a) nodes.push({node,a,b}); offset+=node.length; }
  for (const {node,a,b} of nodes) { const range=document.createRange();range.setStart(node,a);range.setEnd(node,b);const mark=document.createElement('mark');mark.dataset.noteId=id;mark.className=cls;range.surroundContents(mark); }
}
function anchorElement(tid, anchor) { return [...document.querySelectorAll('.annotatable')].find(e=>e.dataset.tid===tid && e.dataset.anchor===anchor); }
function renderNotes() {
  for (const column of document.querySelectorAll('[data-notes]')) {
    const tid=column.dataset.notes;
    const notes=[...state.annotations.filter(n=>n.trace_id===tid).map(n=>({...n,human:true})),...pendingSuggestions().filter(s=>s.trace_id===tid)];
    column.innerHTML=notes.map(n=>`<div class="mnote ${n.human?'':'suggestion'}" data-note-id="${esc(n.id)}" data-anchor="${esc(n.anchor || '')}"><div class="tag">${n.human?'Your note':'AI suggestion'}</div>${n.quote?`<blockquote>${esc(n.quote)}</blockquote>`:''}<p>${esc(n.note || n.mode)}</p>${n.human?`<button data-edit-note="${esc(n.id)}">Edit</button><button data-delete-note="${esc(n.id)}" data-tid="${esc(tid)}">Delete</button>`:`<button data-suggestion="${esc(n.id)}" data-decision="accepted">Accept</button><button data-suggestion="${esc(n.id)}" data-decision="rejected">Reject</button>`}</div>`).join('');
    for (const n of notes) {
      let el=anchorElement(tid,n.anchor);
      // Existing reference annotations may have only a quote and index; don't silently assign an ambiguous match.
      if (!el && n.quote) {const matches=[...document.querySelectorAll('.annotatable')].filter(e=>e.dataset.tid===tid && e.textContent.includes(n.quote));if(matches.length===1)el=matches[0];}
      if (!el || !n.quote) continue;
      let start=n.start, end=n.end;
      if (!Number.isInteger(start) || el.textContent.slice(start,end)!==n.quote) {start=el.textContent.indexOf(n.quote);end=start+n.quote.length;}
      if(start>=0)highlight(el,start,end,n.id,n.human?'':'suggestion');
    }
  }
}
function layoutNotes() {
  for(const col of document.querySelectorAll('[data-notes]')) {
    let floor=0;
    for(const note of col.children) {
      const highlightEl=[...document.querySelectorAll('mark[data-note-id]')].find(e=>e.dataset.noteId===note.dataset.noteId && e.getClientRects().length);
      const anchor=anchorElement(col.dataset.notes,note.dataset.anchor);
      const top=Math.max(floor,(highlightEl || (anchor?.getClientRects().length ? anchor : null))?.getBoundingClientRect().top-col.getBoundingClientRect().top || 0);
      note.style.top=top+'px';floor=top+note.offsetHeight+12;
    }
    col.style.minHeight=floor+'px';
  }
}
function openNote(note) {
  pendingNote=note;$('#note-quote').textContent=note.quote || 'Note for this trace';$('#note-text').value=note.note || '';$('#note-dialog').showModal();$('#note-text').focus();
}
function clearPending() { document.querySelectorAll('mark.pending').forEach(el=>el.replaceWith(document.createTextNode(el.textContent)));pendingNote=null; }
function openMode(mode={}) {
  const form=$('#mode-form');form.reset();
  for(const name of ['name','definition','requirements','example','boundary'])form.elements[name].value=mode[name] || '';
  form.elements.name.readOnly=!!mode.name;form.elements.final.checked=mode.final===true || mode.status==='final';$('#mode-dialog').showModal();
}
function selectedPositive(mode) {
  return [...document.querySelectorAll('[data-positive-select]')].find(select => select.dataset.positiveSelect === mode)?.value;
}
function selectedNegative(mode) {
  return [...document.querySelectorAll('[data-negative-select]')].find(select => select.dataset.negativeSelect === mode)?.value;
}
document.addEventListener('mouseup', event=>{
  if(event.target.closest('dialog,.mnote,button,summary'))return;
  const selection=window.getSelection();if(selection.isCollapsed || !selection.rangeCount)return;
  const range=selection.getRangeAt(0), element=(range.commonAncestorContainer.nodeType===1?range.commonAncestorContainer:range.commonAncestorContainer.parentElement).closest('.annotatable');
  if(!element || !element.contains(range.startContainer) || !element.contains(range.endContainer))return;
  const before=range.cloneRange();before.selectNodeContents(element);before.setEnd(range.startContainer,range.startOffset);
  const start=before.toString().length, quote=range.toString();if(!quote.trim())return;
  highlight(element,start,start+quote.length,'pending','pending');selection.removeAllRanges();
  openNote({trace_id:element.dataset.tid,anchor:element.dataset.anchor,start,end:start+quote.length,quote});
});
document.addEventListener('click', async event=>{
  const button=event.target.closest('button,[data-jump]');if(!button)return;
  try {
    if(button.dataset.view){view=button.dataset.view;render();}
    else if(button.dataset.session){current=button.dataset.session;view='review';renderQueue();render();window.scrollTo(0,0);}
    else if(button.dataset.jump)jump(button.dataset.jump,button.dataset.noteJump);
    else if(button.dataset.addNote)openNote({trace_id:button.dataset.addNote,anchor:'',quote:''});
    else if(button.dataset.editNote){const n=state.annotations.find(n=>n.id===button.dataset.editNote);openNote({...n});}
    else if(button.dataset.deleteNote)await action({kind:'delete_note',id:button.dataset.deleteNote,trace_id:button.dataset.tid});
    else if(button.dataset.reviewed)await action({kind:'reviewed',trace_id:button.dataset.reviewed,outcome:button.dataset.outcome});
    else if(button.dataset.suggestion)await action({kind:'suggestion',id:button.dataset.suggestion,decision:button.dataset.decision});
    else if(button.dataset.editMode)openMode(state.patterns.find(m=>m.name===button.dataset.editMode));
    else if(button.dataset.positiveOpen){const tid=selectedPositive(button.dataset.positiveOpen);if(tid)jump(tid);else notify('Choose a reviewed trace.');}
    else if(button.dataset.positiveAdd){const tid=button.dataset.traceId || selectedPositive(button.dataset.positiveAdd);if(tid)await action({kind:'positive',trace_id:tid,mode:button.dataset.positiveAdd,confirmed:true});else notify('Choose a reviewed trace.');}
    else if(button.dataset.positiveRemove)await action({kind:'positive',trace_id:button.dataset.positiveRemove,mode:button.dataset.mode,confirmed:false});
    else if(button.dataset.negativeOpen){const tid=selectedNegative(button.dataset.negativeOpen);if(tid)jump(tid);else notify('Choose a reviewed trace.');}
    else if(button.dataset.negativeAdd){const tid=selectedNegative(button.dataset.negativeAdd);if(tid)await action({kind:'close_negative',trace_id:tid,mode:button.dataset.negativeAdd,confirmed:true});else notify('Choose a reviewed trace.');}
    else if(button.dataset.negativeRemove)await action({kind:'close_negative',trace_id:button.dataset.negativeRemove,mode:button.dataset.mode,confirmed:false});
    else if(button.dataset.label){
      const field=[...document.querySelectorAll('[data-comment]')].find(e=>e.dataset.comment===button.dataset.tid+':'+button.dataset.mode);
      await action({kind:'judgment',trace_id:button.dataset.tid,mode:button.dataset.mode,label:Number(button.dataset.label),note:field.value},false);
      render();
    }
    else if(button.id==='new-mode')openMode();
    else if(button.id==='cancel-mode')$('#mode-dialog').close();
    else if(button.id==='cancel-note')$('#note-dialog').close();
    else if(button.id==='next-session'){const index=sessions.findIndex(s=>s.id===current);current=sessions[(index+1)%sessions.length]?.id;renderQueue();render();window.scrollTo(0,0);}
    else if(button.id==='retry-sync'){await action({kind:'retry'});notify('Synchronization retry finished. Pending writes remain visible.');}
    else if(button.id==='accept-selected' || button.id==='reject-selected'){
      const ids=[...document.querySelectorAll('[data-suggestion-select]:checked')].map(e=>e.dataset.suggestionSelect);
      for(const id of ids)await action({kind:'suggestion',id,decision:button.id==='accept-selected'?'accepted':'rejected'},false);
      render();
    }
    else if(button.id==='recover'){
      const backup=JSON.parse(localStorage.getItem('cartwheel-review-pending') || '{}');
      for(const [id,payload] of Object.entries(backup)){await action(payload);delete backup[id];localStorage.setItem('cartwheel-review-pending',JSON.stringify(backup));}
      notify('Browser recovery finished.');
    }
    else if(button.id==='refresh'){
      button.disabled=true;button.textContent='Fetching live traces…';
      try{const r=await api('/api/refresh',{});await load();notify(`Loaded ${r.count} live traces.`);}finally{button.disabled=false;button.textContent='Refresh from Langfuse';}
    }
  } catch(error){notify(error.message);}
});
document.addEventListener('keydown',event=>{if(event.key==='Enter' && event.target.matches('circle[data-jump]'))jump(event.target.dataset.jump);});
document.addEventListener('mouseover',event=>{const e=event.target.closest('[data-note-id]');if(e)document.querySelectorAll('[data-note-id]').forEach(n=>{if(n.dataset.noteId===e.dataset.noteId)n.classList.add('linked');});});
document.addEventListener('mouseout',()=>document.querySelectorAll('.linked').forEach(n=>n.classList.remove('linked')));
document.addEventListener('toggle',()=>requestAnimationFrame(layoutNotes),true);
window.addEventListener('resize',layoutNotes);
$('#note-dialog').addEventListener('close',clearPending);
$('#note-form').addEventListener('submit',async event=>{event.preventDefault();try{await action({kind:'note',...pendingNote,note:$('#note-text').value});$('#note-dialog').close();}catch{}});
$('#mode-form').addEventListener('submit',async event=>{event.preventDefault();const form=event.target;const mode=Object.fromEntries(new FormData(form));mode.final=form.elements.final.checked;try{await action({kind:'mode',mode});$('#mode-dialog').close();}catch{}});
document.addEventListener('change',async event=>{
  if(event.target.id==='select-suggestions')document.querySelectorAll('[data-suggestion-select]').forEach(e=>e.checked=event.target.checked);
  if(event.target.dataset.linkNote){const n=state.annotations.find(n=>n.id===event.target.dataset.linkNote);try{await action({kind:'note',...n,mode:event.target.value});}catch{}}
});
for(const id of ['search','role','filter'])$('#'+id).addEventListener(id==='search'?'input':'change',()=>{renderQueue();if(view!=='review')render();});
async function load(){state=await api('/api/data');groupSessions();renderQueue();render();syncStatus();}
load().catch(error=>{$('#main').innerHTML=`<div class="panel error">${esc(error.message)}</div>`;$('#save-status').textContent='Load failed';});
setInterval(async()=>{
  if(!state || busy || document.querySelector('dialog[open]') || ['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName))return;
  try{const next=await api('/api/state');const signature=JSON.stringify(next);if(lastState && signature!==lastState){Object.assign(state,next);renderQueue();render();notify('Review state updated.');}lastState=signature;syncStatus();}catch{ $('#save-status').textContent='Connection interrupted · browser backup available'; }
},10000);
