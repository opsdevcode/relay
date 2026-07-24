import { renderCitationLinks, renderMarkdown } from "./markdown.js";

const API = window.location.origin.includes("3000")
  ? "http://localhost:8080"
  : "";

const chat = document.getElementById("chat");
const form = document.getElementById("composer");
const input = document.getElementById("input");
const statusEl = document.getElementById("status");
const promptsEl = document.getElementById("prompts");

let pendingDraft = null;

const SUGGESTED_PROMPTS = [
  "What are the required resource tags?",
  "What platform services are available?",
  "Create a new service called demo-api",
  "I need a sandbox for a POC",
];

function addMessage(role, text, extraHtml = "") {
  const el = document.createElement("div");
  el.className = `msg ${role}`;
  const body = role === "assistant" ? renderMarkdown(text) : escapeHtml(text);
  el.innerHTML = `<div class="meta">${role === "user" ? "You" : "Assistant"}</div><div class="body">${body}</div>${extraHtml}`;
  chat.appendChild(el);
  chat.scrollTop = chat.scrollHeight;
}

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function formatDraftLabel(draft) {
  if (draft.action === "scaffold_service") {
    const name = draft.inputs?.service_name || draft.service_name || "service";
    return `Scaffold <strong>${escapeHtml(name)}</strong>`;
  }
  if (draft.action === "request_sandbox") {
    return "Request sandbox";
  }
  return escapeHtml(draft.action || "action");
}

function formatActionResult(data) {
  if (data.workflow_url) {
    const inputs = JSON.stringify(data.inputs || {}, null, 2);
    return (
      `<div>${renderMarkdown(data.message || "")}</div>` +
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
      `<div>${renderMarkdown(data.message || "")}</div>` +
      `<div class="draft"><a href="${escapeHtml(data.issue_url)}" target="_blank" rel="noopener">Open issue template</a></div>`
    );
  }
  return escapeHtml(data.message || JSON.stringify(data));
}

async function refreshHealth() {
  try {
    const res = await fetch(`${API}/health`);
    const data = await res.json();
    const mode = data.answer_mode === "llm" ? "LLM" : "extractive (no API keys)";
    const ver = data.version ? ` · v${data.version}` : "";
    statusEl.textContent = `Documents: ${data.documents} · Mode: ${mode}${ver}`;
  } catch {
    statusEl.textContent = "API unreachable — run make up";
  }
}

async function sendMessage(message) {
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
    let extra = renderCitationLinks(data.citations);
    if (data.draft?.requires_confirmation) {
      pendingDraft = data.draft;
      extra += `<div class="draft"><strong>Draft:</strong> ${formatDraftLabel(data.draft)}<br/><button type="button" class="confirm-draft">Confirm</button></div>`;
    }
    addMessage("assistant", data.answer, extra);
    chat.querySelector(".confirm-draft")?.addEventListener("click", confirmDraft);
  } catch (err) {
    addMessage("assistant", `Error: ${err.message}`);
  } finally {
    button.disabled = false;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  await sendMessage(message);
});

async function confirmDraft() {
  if (!pendingDraft) return;
  const res = await fetch(`${API}/actions/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ draft: pendingDraft }),
  });
  const data = await res.json();
  const el = document.createElement("div");
  el.className = "msg assistant";
  el.innerHTML = `<div class="meta">Assistant</div><div class="body">${formatActionResult(data)}</div>`;
  chat.appendChild(el);
  chat.scrollTop = chat.scrollHeight;
  pendingDraft = null;
}

function initPrompts() {
  if (!promptsEl) return;
  for (const prompt of SUGGESTED_PROMPTS) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "prompt-chip";
    btn.textContent = prompt;
    btn.addEventListener("click", () => sendMessage(prompt));
    promptsEl.appendChild(btn);
  }
}

initPrompts();
refreshHealth();
