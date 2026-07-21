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
      extra += `<div class="draft"><strong>Draft action:</strong> ${escapeHtml(data.draft.action)}<br/><button type="button" id="confirm-draft">Confirm</button></div>`;
    }
    addMessage("assistant", data.answer, extra);
    document.getElementById("confirm-draft")?.addEventListener("click", confirmDraft);
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
  addMessage("assistant", data.message || JSON.stringify(data));
  pendingDraft = null;
}

refreshHealth();
