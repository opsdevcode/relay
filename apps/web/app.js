const API = window.location.origin.includes("3000")
  ? "http://localhost:8080"
  : "";

const chat = document.getElementById("chat");
const form = document.getElementById("composer");
const input = document.getElementById("input");
const statusEl = document.getElementById("status");

let pendingDraft = null;

function addMessage(role, text, extra = "") {
  const el = document.createElement("div");
  el.className = `msg ${role}`;
  el.innerHTML = `<div class="meta">${role === "user" ? "You" : "Assistant"}</div>${escapeHtml(text)}${extra}`;
  chat.appendChild(el);
  chat.scrollTop = chat.scrollHeight;
}

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function formatActionResult(data) {
  if (data.workflow_url) {
    const inputs = JSON.stringify(data.inputs || {}, null, 2);
    return (
      `${escapeHtml(data.message || "")}` +
      `<div class="draft">` +
      `<a href="${escapeHtml(data.workflow_url)}" target="_blank" rel="noopener">` +
      `Run workflow: ${escapeHtml(data.workflow_name || "Scaffold K8s Service")}</a>` +
      `<pre class="inputs">${escapeHtml(inputs)}</pre>` +
      `<p class="hint">Paste these values into the workflow form if they are not pre-filled.</p>` +
      `</div>`
    );
  }
  if (data.issue_url) {
    return (
      `${escapeHtml(data.message || "")} ` +
      `<div class="draft"><a href="${escapeHtml(data.issue_url)}" target="_blank" rel="noopener">Open issue template</a></div>`
    );
  }
  return escapeHtml(data.message || JSON.stringify(data));
}

async function refreshHealth() {
  try {
    const res = await fetch(`${API}/health`);
    const data = await res.json();
    statusEl.textContent = `Indexed documents: ${data.documents}`;
  } catch {
    statusEl.textContent = "API unreachable — is portal-assistant running?";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  addMessage("user", message);
  input.value = "";
  pendingDraft = null;

  const button = form.querySelector("button");
  button.disabled = true;

  try {
    const res = await fetch(`${API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await res.json();
    let extra = "";
    if (data.citations?.length) {
      extra += `\n\nSources:\n${data.citations.map((c) => `- ${c.source}`).join("\n")}`;
    }
    if (data.draft?.requires_confirmation) {
      pendingDraft = data.draft;
      extra += `<div class="draft"><strong>Draft action:</strong> ${escapeHtml(data.draft.action)}<br/><button type="button" class="confirm-draft">Confirm</button></div>`;
    }
    addMessage("assistant", data.answer, extra);
    document.querySelector(".confirm-draft")?.addEventListener("click", confirmDraft);
  } catch (err) {
    addMessage("assistant", `Error: ${err.message}`);
  } finally {
    button.disabled = false;
  }
});

async function confirmDraft() {
  if (!pendingDraft) return;
  const res = await fetch(`${API}/actions/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ draft: pendingDraft }),
  });
  const data = await res.json();
  addMessage("assistant", "", formatActionResult(data));
  pendingDraft = null;
}

refreshHealth();
