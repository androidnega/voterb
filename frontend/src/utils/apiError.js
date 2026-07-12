/**
 * Turn a DRF/axios error into a user-facing message.
 */
export function parseApiError(error, fallback = 'Something went wrong. Please try again.') {
  const data = error?.response?.data
  if (!data) return fallback

  if (typeof data.error === 'string') return data.error
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) return data.detail.join(' ')

  const parts = []
  for (const value of Object.values(data)) {
    if (Array.isArray(value)) parts.push(value.join(', '))
    else if (value != null) parts.push(String(value))
  }
  if (parts.length) return parts.join(' ')

  return fallback
}
