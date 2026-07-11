/** Display index without slashes (storage still uses SC/2021/PL/001). */
export function formatIndexDisplay(index) {
  if (!index) return '—'
  return String(index).replace(/\//g, '')
}

/** Normalize index for search — ignores slashes and case. */
export function normalizeIndex(value) {
  return (value || '').trim().toLowerCase().replace(/\//g, '')
}
