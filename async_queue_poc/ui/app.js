const queueListEl = document.getElementById("queue-list");
const selectedQueueEl = document.getElementById("selected-queue");
const activityLogEl = document.getElementById("activity-log");
const transportLogEl = document.getElementById("transport-log");

const queueNameInput = document.getElementById("queue-name-input");
const itemInput = document.getElementById("item-input");

let selectedQueueName = null;
const activityLog = [];

function logActivity(message) {
  activityLog.unshift(`${new Date().toLocaleTimeString()} - ${message}`);
  if (activityLog.length > 30) {
    activityLog.pop();
  }
  renderActivityLog();
}

function renderActivityLog() {
  activityLogEl.innerHTML = "";
  for (const entry of activityLog) {
    const li = document.createElement("li");
    li.textContent = entry;
    activityLogEl.appendChild(li);
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
      <strong>${queue.name}</strong><br />
      ${queue.state}<br />
      items: ${queue.item_count}
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
    ? `<ul>${snapshot.items.map((item) => `<li>${item} &nbsp; <em>PENDING</em></li>`).join("")}</ul>`
    : "<p>No pending items.</p>";

  selectedQueueEl.innerHTML = `
    <p><strong>Name:</strong> ${snapshot.name}</p>
    <p><strong>State:</strong> ${snapshot.state}</p>
    <p><strong>Items:</strong> ${snapshot.size}</p>
    ${itemsMarkup}
  `;
}

function renderTransportLog(entries) {
  transportLogEl.innerHTML = "";
  if (!entries.length) {
    transportLogEl.innerHTML = "<li>No dispatched items yet.</li>";
    return;
  }

  for (const entry of entries) {
    const li = document.createElement("li");
    li.textContent = `${entry.queue} → ${entry.item} (${entry.timestamp})`;
    transportLogEl.appendChild(li);
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
  }

  const transportEntries = await requestJson("/transport/log");
  renderTransportLog(transportEntries);
}

async function withAction(action, successMessage) {
  try {
    await action();
    logActivity(successMessage);
    await refreshAll();
  } catch (error) {
    logActivity(`Error: ${error.message}`);
  }
}

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
    async () => requestJson(`/queues/${selectedQueueName}/items`, {
      method: "POST",
      body: JSON.stringify({ item }),
    }),
    `Item added to ${selectedQueueName}: ${item}`
  );
});

document.getElementById("dispatch-btn").addEventListener("click", async () => {
  if (!selectedQueueName) return;
  await withAction(async () => {
    const payload = await requestJson(`/queues/${selectedQueueName}/dispatch`, { method: "POST" });
    if (payload.dispatched_item) {
      logActivity(`Item dispatched from ${selectedQueueName}: ${payload.dispatched_item}`);
    } else {
      logActivity(`No item dispatched for ${selectedQueueName}`);
    }
  }, `Dispatch requested: ${selectedQueueName}`);
});

document.getElementById("refresh-btn").addEventListener("click", () => {
  withAction(async () => {}, "Manual refresh");
});

refreshAll().catch((error) => logActivity(`Error: ${error.message}`));
