/**
 * Shared helper functions — add to this file as new sections need them.
 */

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
