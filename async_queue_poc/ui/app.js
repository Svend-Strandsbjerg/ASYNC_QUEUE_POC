const queueListEl = document.getElementById("queue-list");
const selectedQueueEl = document.getElementById("selected-queue");
const activityLogEl = document.getElementById("activity-log");
const transportLogEl = document.getElementById("transport-log");

const queueNameInput = document.getElementById("queue-name-input");
const itemInput = document.getElementById("item-input");

let selectedQueueId = null;
const MAX_ACTIVITY_LOG_ENTRIES = 80;

function prependLogEntry(container, element) {
  container.insertBefore(element, container.firstChild);
}

function clearLog(container, emptyMessage) {
  container.innerHTML = "";
  const li = document.createElement("li");
  li.textContent = emptyMessage;
  li.dataset.emptyState = "true";
  container.appendChild(li);
}

function logActivity(message) {
  const emptyState = activityLogEl.querySelector("li[data-empty-state='true']");
  if (emptyState) {
    emptyState.remove();
  }

  const li = document.createElement("li");
  li.textContent = `${new Date().toLocaleTimeString()} - ${message}`;
  prependLogEntry(activityLogEl, li);

  while (activityLogEl.children.length > MAX_ACTIVITY_LOG_ENTRIES) {
    activityLogEl.lastElementChild?.remove();
  }
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw new Error(errorPayload.detail || `Request failed (${response.status})`);
  }

  return response.json();
}

function queueStateBadge(state) {
  const tone = state === "PAUSED" ? "badge-paused" : "badge-open";
  return `<span class="state-badge ${tone}">${state}</span>`;
}

function queueTitle(queue) {
  return queue.queue_name || queue.name || queue.queue_id;
}

function renderQueueList(queues) {
  queueListEl.innerHTML = "";

  if (!queues.length) {
    queueListEl.innerHTML = "<p>No queues created yet.</p>";
    return;
  }

  for (const queue of queues) {
    const card = document.createElement("div");
    card.className = "queue-card";
    if (queue.queue_id === selectedQueueId) {
      card.classList.add("active");
    }
    card.innerHTML = `
      <div class="queue-header">
        <strong>${queueTitle(queue)}</strong>
        ${queueStateBadge(queue.state)}
      </div>
      <small>ID: ${queue.queue_id}</small><br />
      <small>pending: ${queue.item_count}</small><br />
      <small>sent: ${queue.sent_item_count}</small>
    `;
    card.addEventListener("click", async () => {
      selectedQueueId = queue.queue_id;
      await refreshAll();
    });
    queueListEl.appendChild(card);
  }
}

function renderSelectedQueue(snapshot) {
  if (!snapshot) {
    selectedQueueEl.innerHTML = "<p>No queue selected.</p>";
    return;
  }

  const itemsMarkup = snapshot.items.length
    ? `<ul>${snapshot.items
        .map(
          (item) =>
            `<li>${item.payload} (item_id=${item.item_id}) &nbsp; <em class="item-status-${item.status.toLowerCase()}">${item.status}</em></li>`
        )
        .join("")}</ul>`
    : "<p>No items in queue.</p>";

  selectedQueueEl.innerHTML = `
    <p><strong>Name:</strong> ${snapshot.queue_name}</p>
    <p><strong>Queue ID:</strong> ${snapshot.queue_id}</p>
    <p><strong>State:</strong> ${queueStateBadge(snapshot.state)}</p>
    <p><strong>Pending:</strong> ${snapshot.size}</p>
    <p><strong>Sent:</strong> ${snapshot.sent_count}</p>
    ${itemsMarkup}
  `;
}

function formatReleasedAt(releasedAt) {
  const releaseDate = new Date(releasedAt);
  if (Number.isNaN(releaseDate.getTime())) {
    return releasedAt;
  }

  const pad = (value) => String(value).padStart(2, "0");
  return `${releaseDate.getFullYear()}-${pad(releaseDate.getMonth() + 1)}-${pad(releaseDate.getDate())} ${pad(releaseDate.getHours())}:${pad(releaseDate.getMinutes())}:${pad(releaseDate.getSeconds())}`;
}

function renderTransportLog(entries) {
  clearLog(transportLogEl, "No sent items yet.");
  if (!entries.length) {
    return;
  }

  transportLogEl.innerHTML = "";

  for (const entry of entries) {
    const li = document.createElement("li");
    const releasedAt = entry.released_at || entry.sent_at || entry.timestamp;
    li.innerHTML = `
      <article class="log-entry" data-testid="sent-log-entry">
        <div class="log-entry-header">Item ID: ${entry.item_id}</div>
        <div class="log-entry-body">
          <div>Queue ID: ${entry.queue_id}</div>
          <div>Released: ${formatReleasedAt(releasedAt)}</div>
        </div>
      </article>
    `;
    prependLogEntry(transportLogEl, li);
  }
}

async function refreshAll() {
  const queues = await requestJson("/queues");
  renderQueueList(queues);

  if (selectedQueueId) {
    try {
      const snapshot = await requestJson(`/queues/${selectedQueueId}`);
      renderSelectedQueue(snapshot);
    } catch (_error) {
      selectedQueueId = null;
      renderSelectedQueue(null);
    }
  } else {
    renderSelectedQueue(null);
  }

  const transportEntries = await requestJson("/transport/log");
  renderTransportLog(transportEntries);
}

async function withAction(action, successMessage) {
  try {
    await action();
    if (successMessage) {
      logActivity(successMessage);
    }
    await refreshAll();
  } catch (error) {
    logActivity(`Error: ${error.message}`);
  }
}

document.getElementById("run-test-btn").addEventListener("click", async () => {
  await withAction(async () => {
    logActivity("Run Test started");
    const payload = await requestJson("/test/run", { method: "POST" });

    for (const result of payload.results) {
      logActivity(`Queue processing started: queue_id=${result.queue_id}`);
      if (result.status === "SKIPPED") {
        logActivity(`Queue skipped because paused: queue_id=${result.queue_id}`);
      } else {
        for (const item of result.items_sent) {
          logActivity(`Item sent: item_id=${item.item_id}, queue_id=${result.queue_id}`);
        }
      }
      logActivity(`Queue processing completed: queue_id=${result.queue_id}`);
    }

    logActivity(
      `Run Test completed: processed=${payload.processed.queues} (${payload.processed.items} items), skipped=${payload.skipped.queues} (${payload.skipped.items} items), sent=${payload.sent.queues} (${payload.sent.items} items)`
    );
  });
});

document.getElementById("create-queue-btn").addEventListener("click", async () => {
  const queueName = queueNameInput.value.trim();
  if (!queueName) {
    logActivity("Queue name is required");
    return;
  }

  await withAction(async () => {
    const queue = await requestJson("/queues", {
      method: "POST",
      body: JSON.stringify({ name: queueName }),
    });
    selectedQueueId = queue.queue_id;
    logActivity(`Queue created: queue_id=${queue.queue_id}, name=${queue.queue_name}`);
  });
});

document.getElementById("pause-btn").addEventListener("click", async () => {
  if (!selectedQueueId) return;
  await withAction(async () => {
    const queue = await requestJson(`/queues/${selectedQueueId}/pause`, { method: "POST" });
    logActivity(`Queue paused: queue_id=${queue.queue_id}`);
  });
});

document.getElementById("resume-btn").addEventListener("click", async () => {
  if (!selectedQueueId) return;
  await withAction(async () => {
    const queue = await requestJson(`/queues/${selectedQueueId}/resume`, { method: "POST" });
    logActivity(`Queue resumed: queue_id=${queue.queue_id}`);
  });
});

document.getElementById("add-item-btn").addEventListener("click", async () => {
  if (!selectedQueueId) return;
  const item = itemInput.value.trim();
  if (!item) {
    logActivity("Item payload is required");
    return;
  }

  await withAction(async () => {
    const response = await requestJson(`/queues/${selectedQueueId}/items`, {
      method: "POST",
      body: JSON.stringify({ item }),
    });
    logActivity(`Item added: item_id=${response.item.item_id}, queue_id=${response.item.queue_id}`);
  });
});

document.getElementById("refresh-btn").addEventListener("click", () => {
  withAction(async () => {}, "Manual refresh");
});

clearLog(activityLogEl, "No activity yet.");
refreshAll().catch((error) => logActivity(`Error: ${error.message}`));
