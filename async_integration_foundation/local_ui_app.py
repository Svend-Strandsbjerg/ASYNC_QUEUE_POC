from __future__ import annotations

from copy import deepcopy
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from async_integration_foundation.queue_framework import InMemoryQueueRepository, FakeTransport, QueueItemState


class ScopePayload(BaseModel):
    session_id: str
    user_id: str
    context_type: str
    context_id: str

    def as_scope(self) -> dict[str, str]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "context_type": self.context_type,
            "context_id": self.context_id,
        }


class AddItemPayload(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


def _queue_summary(queue: Any) -> dict[str, Any]:
    snapshot = queue.snapshot()
    return {
        "queue_id": snapshot["queue_id"],
        "scope": snapshot["scope"],
        "queue_state": snapshot["queue_state"],
        "item_count": snapshot["item_count"],
        "pending_items": sum(1 for item in snapshot["items"] if item["state"] == QueueItemState.PENDING.value),
        "has_dispatched_items": any(item["state"] == QueueItemState.DISPATCHED.value for item in snapshot["items"]),
    }


def create_app() -> FastAPI:
    app = FastAPI(title="Async Queue POC Local UI")
    repository = InMemoryQueueRepository()
    transport = FakeTransport()

    def find_queue(queue_id: str):
        for queue in repository.list_queues():
            if queue.id == queue_id:
                return queue
        raise HTTPException(status_code=404, detail=f"Queue '{queue_id}' not found")

    @app.get("/", response_class=HTMLResponse)
    def ui() -> str:
        return HTML_TEMPLATE

    @app.get("/api/queues")
    def list_queues() -> dict[str, Any]:
        queues = [_queue_summary(queue) for queue in repository.list_queues()]
        return {"queues": queues, "count": len(queues)}

    @app.post("/api/queues/get-or-create")
    def get_or_create_queue(payload: ScopePayload) -> dict[str, Any]:
        queue = repository.get_or_create_queue(payload.as_scope())
        return {"queue": _queue_summary(queue), "snapshot": queue.snapshot()}

    @app.post("/api/queues/{queue_id}/pause")
    def pause_queue(queue_id: str) -> dict[str, Any]:
        queue = find_queue(queue_id)
        queue.pause()
        return {"snapshot": queue.snapshot()}

    @app.post("/api/queues/{queue_id}/resume")
    def resume_queue(queue_id: str) -> dict[str, Any]:
        queue = find_queue(queue_id)
        queue.resume()
        return {"snapshot": queue.snapshot()}

    @app.post("/api/queues/{queue_id}/items")
    def add_item(queue_id: str, payload: AddItemPayload) -> dict[str, Any]:
        queue = find_queue(queue_id)
        item = queue.add_item(payload.payload)
        return {
            "item": {
                "item_id": item.id,
                "state": item.state.value,
                "dispatch_attempts": item.dispatch_attempts,
                "payload": deepcopy(item.payload),
            },
            "snapshot": queue.snapshot(),
        }

    @app.post("/api/queues/{queue_id}/dispatch")
    def dispatch_queue(queue_id: str) -> dict[str, Any]:
        queue = find_queue(queue_id)
        dispatched = queue.dispatch_all(transport)
        return {"dispatched": dispatched, "snapshot": queue.snapshot()}

    @app.get("/api/queues/{queue_id}/snapshot")
    def get_snapshot(queue_id: str) -> dict[str, Any]:
        queue = find_queue(queue_id)
        return {"snapshot": queue.snapshot()}

    @app.get("/api/sent-log")
    def sent_log(queue_id: str | None = Query(default=None)) -> dict[str, Any]:
        entries = deepcopy(transport.sent)
        if queue_id:
            entries = [entry for entry in entries if entry["queue_id"] == queue_id]
        return {"count": len(entries), "entries": entries}

    return app


app = create_app()


HTML_TEMPLATE = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Async Queue POC UI</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f6f7f9; }
    .layout { display: grid; grid-template-columns: 1fr 1.2fr 1.2fr; gap: 12px; padding: 12px; height: 100vh; box-sizing: border-box; }
    .col { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 12px; overflow: auto; }
    .logs-col { display: flex; flex-direction: column; gap: 10px; }
    .log-panel {
      border: 1px solid #ddd;
      border-radius: 6px;
      background: #f9fafb;
      display: flex;
      flex-direction: column;
      height: 260px;
      min-height: 0;
    }
    .log-panel-header { margin: 0; padding: 8px 10px; border-bottom: 1px solid #ddd; font-size: 15px; }
    .log-panel-body {
      margin: 0;
      flex: 1;
      min-height: 0;
      overflow-y: auto;
      overflow-x: auto;
      background: #111827;
      color: #e5e7eb;
      padding: 8px;
      border-radius: 0 0 6px 6px;
      font-size: 12px;
    }
    h2 { margin-top: 0; }
    .queue { border: 1px solid #ddd; border-radius: 6px; padding: 8px; margin-bottom: 8px; cursor: pointer; }
    .queue.selected { border-color: #2563eb; background: #eef4ff; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; background: #e5e7eb; }
    .badge.OPEN { background: #dcfce7; }
    .badge.PAUSED { background: #fee2e2; }
    .badge.DISPATCHING { background: #dbeafe; }
    .row { margin-bottom: 8px; }
    label { display: block; font-size: 12px; color: #555; }
    input, textarea, button { width: 100%; box-sizing: border-box; margin-top: 2px; margin-bottom: 6px; }
    textarea { min-height: 70px; }
    pre { background: #111827; color: #e5e7eb; padding: 8px; border-radius: 6px; overflow: auto; font-size: 12px; }
    .actions { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
    .mini { font-size: 12px; color: #444; }
  </style>
</head>
<body>
  <div class=\"layout\">
    <div class=\"col\">
      <h2>Queues</h2>
      <div id=\"queues\"></div>
    </div>

    <div class=\"col\">
      <h2>Selected Queue</h2>
      <div class=\"row\">
        <label>session_id</label><input id=\"session_id\" value=\"sess-001\" />
        <label>user_id</label><input id=\"user_id\" value=\"alice\" />
        <label>context_type</label><input id=\"context_type\" value=\"ORDER\" />
        <label>context_id</label><input id=\"context_id\" value=\"ORD-9001\" />
        <button onclick=\"getOrCreateQueue()\">Create/Get Queue</button>
      </div>
      <div class=\"actions\">
        <button onclick=\"pauseQueue()\">Pause</button>
        <button onclick=\"resumeQueue()\">Resume</button>
        <button onclick=\"dispatchQueue()\">Dispatch</button>
        <button onclick=\"refreshSnapshot()\">Refresh Snapshot</button>
      </div>
      <div class=\"row\">
        <label>Item payload (JSON)</label>
        <textarea id=\"item_payload\">{"value": "demo-item"}</textarea>
        <button onclick=\"addItem()\">Add Item</button>
      </div>
      <div id=\"selected_queue\" class=\"mini\">No queue selected.</div>
      <pre id=\"snapshot\">{}</pre>
    </div>

    <div class=\"col logs-col\">
      <h2>Logs / Sent via Dummy API</h2>
      <div class=\"log-panel\" data-testid=\"activity-log-panel\">
        <h3 class=\"log-panel-header\">Activity log (selected queue)</h3>
        <pre id=\"activity_log\" class=\"log-panel-body\">[]</pre>
      </div>
      <div class=\"log-panel\" data-testid=\"sent-log-panel\">
        <h3 class=\"log-panel-header\">Sent log (fake transport)</h3>
        <pre id=\"sent_log\" class=\"log-panel-body\">[]</pre>
      </div>
    </div>
  </div>

<script>
let selectedQueueId = null;

function scopePayload() {
  return {
    session_id: document.getElementById('session_id').value,
    user_id: document.getElementById('user_id').value,
    context_type: document.getElementById('context_type').value,
    context_id: document.getElementById('context_id').value,
  };
}

async function api(path, method='GET', body=null) {
  const res = await fetch(path, {
    method,
    headers: {'Content-Type': 'application/json'},
    body: body ? JSON.stringify(body) : null,
  });
  if (!res.ok) {
    alert(`API error ${res.status}`);
    throw new Error(await res.text());
  }
  return await res.json();
}

function queueCard(queue) {
  const selectedClass = queue.queue_id === selectedQueueId ? 'selected' : '';
  const historical = queue.has_dispatched_items ? ' +historical dispatched' : '';
  return `<div class="queue ${selectedClass}" onclick="selectQueue('${queue.queue_id}')">
    <div><strong>${queue.queue_id}</strong></div>
    <div class="mini">${queue.scope.session_id} / ${queue.scope.user_id} / ${queue.scope.context_type} / ${queue.scope.context_id}</div>
    <div><span class="badge ${queue.queue_state}">${queue.queue_state}</span> <span class="mini">items:${queue.item_count} pending:${queue.pending_items}${historical}</span></div>
  </div>`;
}

async function refreshQueues() {
  const data = await api('/api/queues');
  document.getElementById('queues').innerHTML = data.queues.map(queueCard).join('') || '<div class="mini">No queues yet.</div>';
}

function setSelectedSnapshot(snapshot) {
  selectedQueueId = snapshot.queue_id;
  document.getElementById('selected_queue').innerHTML = `<strong>${snapshot.queue_id}</strong> - <span class="badge ${snapshot.queue_state}">${snapshot.queue_state}</span><br>${snapshot.scope.session_id} / ${snapshot.scope.user_id} / ${snapshot.scope.context_type} / ${snapshot.scope.context_id}`;
  document.getElementById('snapshot').textContent = JSON.stringify(snapshot.items, null, 2);
  document.getElementById('activity_log').textContent = JSON.stringify(snapshot.activity_log, null, 2);
}

async function refreshSentLog() {
  const query = selectedQueueId ? `?queue_id=${selectedQueueId}` : '';
  const sent = await api('/api/sent-log' + query);
  document.getElementById('sent_log').textContent = JSON.stringify(sent, null, 2);
}

async function getOrCreateQueue() {
  const data = await api('/api/queues/get-or-create', 'POST', scopePayload());
  setSelectedSnapshot(data.snapshot);
  await refreshQueues();
  await refreshSentLog();
}

async function selectQueue(queueId) {
  selectedQueueId = queueId;
  const data = await api(`/api/queues/${queueId}/snapshot`);
  setSelectedSnapshot(data.snapshot);
  await refreshQueues();
  await refreshSentLog();
}

async function pauseQueue() {
  if (!selectedQueueId) return;
  const data = await api(`/api/queues/${selectedQueueId}/pause`, 'POST');
  setSelectedSnapshot(data.snapshot);
  await refreshQueues();
}

async function resumeQueue() {
  if (!selectedQueueId) return;
  const data = await api(`/api/queues/${selectedQueueId}/resume`, 'POST');
  setSelectedSnapshot(data.snapshot);
  await refreshQueues();
}

async function addItem() {
  if (!selectedQueueId) return;
  const raw = document.getElementById('item_payload').value;
  const payload = JSON.parse(raw || '{}');
  const data = await api(`/api/queues/${selectedQueueId}/items`, 'POST', {payload});
  setSelectedSnapshot(data.snapshot);
  await refreshQueues();
  await refreshSentLog();
}

async function dispatchQueue() {
  if (!selectedQueueId) return;
  const data = await api(`/api/queues/${selectedQueueId}/dispatch`, 'POST');
  setSelectedSnapshot(data.snapshot);
  await refreshQueues();
  await refreshSentLog();
}

async function refreshSnapshot() {
  if (!selectedQueueId) return;
  const data = await api(`/api/queues/${selectedQueueId}/snapshot`);
  setSelectedSnapshot(data.snapshot);
  await refreshQueues();
  await refreshSentLog();
}

refreshQueues();
refreshSentLog();
</script>
</body>
</html>
"""
