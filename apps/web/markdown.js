/** Minimal markdown → HTML (assistant answers; user content stays escaped). */
export function renderMarkdown(text) {
  if (!text) return "";

  let html = escapeHtml(text);

  html = html.replace(/^### (.+)$/gm, "<h4>$1</h4>");
  html = html.replace(/^## (.+)$/gm, "<h3>$1</h3>");
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

  html = html.replace(/(^|\n)(- .+(?:\n- .+)*)/g, (_, prefix, block) => {
    const items = block
      .split("\n")
      .map((line) => `<li>${line.slice(2)}</li>`)
      .join("");
    return `${prefix}<ul>${items}</ul>`;
  });

  html = html.replace(/\n\n/g, "</p><p>");
  html = `<p>${html}</p>`;
  html = html.replace(/<p><\/p>/g, "");
  html = html.replace(/<p>(<h[34]>)/g, "$1");
  html = html.replace(/(<\/h[34]>)<\/p>/g, "$1");
  html = html.replace(/<p>(<ul>)/g, "$1");
  html = html.replace(/(<\/ul>)<\/p>/g, "$1");

  return html;
}

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

export function renderCitationLinks(citations) {
  if (!citations?.length) return "";
  const items = citations
    .map((c) => {
      const label = c.title || c.source;
      return `<li><code>${escapeHtml(c.source)}</code> — ${escapeHtml(label)}</li>`;
    })
    .join("");
  return `<div class="citations"><strong>Sources</strong><ul>${items}</ul></div>`;
}
