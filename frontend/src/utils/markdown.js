/** 轻量 Markdown 渲染（AI 回复常用格式） */
export function renderSimpleMarkdown(text) {
  if (!text) return ''

  let html = escapeHtml(String(text))

  html = html.replace(/^### (.+)$/gm, '<h4 class="md-h4">$1</h4>')
  html = html.replace(/^## (.+)$/gm, '<h3 class="md-h3">$1</h3>')
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/^\d+\.\s+(.+)$/gm, '<li class="md-ol">$1</li>')
  html = html.replace(/^[-*]\s+(.+)$/gm, '<li class="md-ul">$1</li>')
  html = html.replace(/\n/g, '<br>')

  return html
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}
