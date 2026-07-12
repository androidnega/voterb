/**
 * Resolve a media path from the API into a browser-loadable URL.
 * API returns paths like "/media/candidate_photos/foo.png".
 */
export function resolveMediaUrl(url) {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url
  }
  if (url.startsWith('/')) return url
  return `/${url.replace(/^\//, '')}`
}
