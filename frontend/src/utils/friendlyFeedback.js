/**
 * User-facing copy for network / API failures.
 * Never surfaces status codes, stack traces, or raw backend payloads.
 */

const SAFE_ACTION_HINTS = [
  { test: /invalid|incorrect|wrong|expired|mismatch/i, message: 'That code doesn’t look right. Double-check and try again.' },
  { test: /already\s+(voted|cast)|already\s+submitted/i, message: 'You’ve already cast your vote for this election.' },
  { test: /not\s+eligible|ineligible/i, message: 'You’re not eligible for this ballot.' },
  { test: /cooldown|too\s+many|rate\s+limit|try\s+again\s+later/i, message: 'Please wait a moment, then try again.' },
  { test: /closed|not\s+open|ended/i, message: 'This ballot isn’t open for voting right now.' },
  { test: /presence\s+photo|presence\s+check|audit\s+presence/i, message: 'Take a quick presence photo first, then continue to your ballot.' },
  { test: /valid\s+svt|secure\s+voting\s+token|validate\s+your\s+secure/i, message: 'Validate your Secure Voting Token to continue.' },
]

function isLikelyTechnical(text) {
  if (!text || typeof text !== 'string') return true
  const t = text.trim()
  if (t.length > 160) return true
  if (/traceback|exception|sql|django|drf|axios|etype|undefined|null\b|\{|\}|\[|\]/i.test(t)) return true
  if (/^\d{3}\s/.test(t)) return true
  return false
}

export function isOffline() {
  return typeof navigator !== 'undefined' && navigator.onLine === false
}

export function friendlyLoadError(error, subject = 'this page') {
  if (isOffline()) {
    return 'You’re offline. Reconnect to the internet, then try again.'
  }

  if (!error?.response) {
    if (error?.code === 'ECONNABORTED' || /timeout/i.test(error?.message || '')) {
      return 'This is taking longer than usual. Please try again.'
    }
    return 'We couldn’t reach the server. Check your connection and try again.'
  }

  const status = error.response.status
  if (status === 401) return 'Your session expired. Please sign in again.'
  if (status === 403) return 'You don’t have access to this right now.'
  if (status === 404) return 'We couldn’t find what you’re looking for.'
  if (status === 429) return 'Please wait a moment, then try again.'
  if (status >= 500) return 'Something went wrong on our side. Please try again in a moment.'

  const raw = error.response?.data?.error || error.response?.data?.detail
  if (typeof raw === 'string' && !isLikelyTechnical(raw)) {
    for (const hint of SAFE_ACTION_HINTS) {
      if (hint.test.test(raw)) return hint.message
    }
    if (raw.length <= 120 && !/[<>_/\\]{2,}/.test(raw)) return raw
  }

  return `We couldn’t load ${subject}. Please try again.`
}

export function friendlyActionError(error, fallback = 'Something went wrong. Please try again.') {
  if (isOffline()) {
    return 'You’re offline. Reconnect to the internet, then try again.'
  }

  if (!error?.response) {
    if (error?.code === 'ECONNABORTED' || /timeout/i.test(error?.message || '')) {
      return 'This is taking longer than usual. Please try again.'
    }
    return 'We couldn’t reach the server. Check your connection and try again.'
  }

  const status = error.response.status
  if (status === 401) return 'Your session expired. Please sign in again.'
  if (status === 403) return 'You don’t have permission to do that.'
  if (status === 429) {
    const raw429 = error.response?.data?.error || error.response?.data?.detail
    if (typeof raw429 === 'string' && /wait|moment|later|try again/i.test(raw429) && !isLikelyTechnical(raw429)) {
      return raw429
    }
    return 'Please wait a moment, then try again.'
  }
  if (status >= 500) return 'Something went wrong on our side. Please try again in a moment.'

  const raw = error.response?.data?.error || error.response?.data?.detail
  if (typeof raw === 'string' && !isLikelyTechnical(raw)) {
    for (const hint of SAFE_ACTION_HINTS) {
      if (hint.test.test(raw)) return hint.message
    }
    // Short, plain server copy that already reads human-friendly
    if (raw.length <= 90 && !/[<>_/\\]{2,}/.test(raw)) return raw
  }

  return fallback
}

export const SLOW_LOAD_HINT = 'Still working — thanks for waiting.'
