const queueListEl = document.getElementById("queue-list");
const selectedQueueEl = document.getElementById("selected-queue");
const activityLogEl = document.getElementById("activity-log");
const transportLogEl = document.getElementById("transport-log");

const queueNameInput = document.getElementById("queue-name-input");
const itemInput = document.getElementById("item-input");

let selectedQueueName = null;
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

function renderQueueList(queues) {
  queueListEl.innerHTML = "";

  if (!queues.length) {
    queueListEl.innerHTML = "<p>No queues created yet.</p>";
    return;
  }

  for (const queue of queues) {
    const card = document.createElement("div");
    card.className = "queue-card";
    if (queue.name === selectedQueueName) {
      card.classList.add("active");
    }
    card.innerHTML = `
      <div class="queue-header">
        <strong>${queue.name}</strong>
        ${queueStateBadge(queue.state)}
      </div>
      <small>pending: ${queue.item_count}</small><br />
      <small>sent: ${queue.sent_item_count}</small>
    `;
    card.addEventListener("click", async () => {
      selectedQueueName = queue.name;
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
            `<li>${item.payload} &nbsp; <em class="item-status-${item.status.toLowerCase()}">${item.status}</em></li>`
        )
        .join("")}</ul>`
    : "<p>No items in queue.</p>";

  selectedQueueEl.innerHTML = `
    <p><strong>Name:</strong> ${snapshot.name}</p>
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
    const itemId = entry.item_id || entry.item;
    const queueId = entry.queue_id || entry.queue;
    li.innerHTML = `
      <article class="log-entry" data-testid="sent-log-entry">
        <div class="log-entry-header">Item: ${itemId}</div>
        <div class="log-entry-body">
          <div>Queue: ${queueId}</div>
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

  if (selectedQueueName) {
    try {
      const snapshot = await requestJson(`/queues/${selectedQueueName}`);
      renderSelectedQueue(snapshot);
    } catch (_error) {
      selectedQueueName = null;
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
      logActivity(`Queue processing started: ${result.queue}`);
      if (result.status === "SKIPPED") {
        logActivity(`Queue skipped because paused: ${result.queue}`);
      } else {
        for (const item of result.items_sent) {
          logActivity(`Item sent: ${result.queue} → ${item}`);
        }
      }
      logActivity(`Queue processing completed: ${result.queue}`);
    }

    logActivity(
      `Run Test completed: processed=${payload.queues_processed}, skipped=${payload.queues_skipped}, sent=${payload.items_sent}`
    );
  });
});

document.getElementById("create-queue-btn").addEventListener("click", async () => {
  const queueName = queueNameInput.value.trim();
  if (!queueName) {
    logActivity("Queue name is required");
    return;
  }

  await withAction(
    async () => {
      await requestJson("/queues", {
        method: "POST",
        body: JSON.stringify({ name: queueName }),
      });
      selectedQueueName = queueName;
    },
    `Queue created: ${queueName}`
  );
});

document.getElementById("pause-btn").addEventListener("click", async () => {
  if (!selectedQueueName) return;
  await withAction(
    async () => requestJson(`/queues/${selectedQueueName}/pause`, { method: "POST" }),
    `Queue paused: ${selectedQueueName}`
  );
});

document.getElementById("resume-btn").addEventListener("click", async () => {
  if (!selectedQueueName) return;
  await withAction(
    async () => requestJson(`/queues/${selectedQueueName}/resume`, { method: "POST" }),
    `Queue resumed: ${selectedQueueName}`
  );
});

document.getElementById("add-item-btn").addEventListener("click", async () => {
  if (!selectedQueueName) return;
  const item = itemInput.value.trim();
  if (!item) {
    logActivity("Item payload is required");
    return;
  }

  await withAction(
    async () =>
      requestJson(`/queues/${selectedQueueName}/items`, {
        method: "POST",
        body: JSON.stringify({ item }),
      }),
    `Item added to ${selectedQueueName}: ${item}`
  );
});

document.getElementById("refresh-btn").addEventListener("click", () => {
  withAction(async () => {}, "Manual refresh");
});

clearLog(activityLogEl, "No activity yet.");
refreshAll().catch((error) => logActivity(`Error: ${error.message}`));
