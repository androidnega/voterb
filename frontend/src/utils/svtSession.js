const SVT_PATTERN = /^v-[a-z]{3}-\d{4}$/

function storageKey(electionUuid) {
  return `svt:${electionUuid}`
}

export function normalizeSvt(code) {
  const raw = String(code || '').trim().toLowerCase().replace(/\s+/g, '')
  const compact = raw.replace(/-/g, '')
  if (/^v[a-z]{3}\d{4}$/.test(compact)) {
    return `v-${compact.slice(1, 4)}-${compact.slice(4)}`
  }
  return raw
}

export function isValidSvtFormat(code) {
  return SVT_PATTERN.test(normalizeSvt(code))
}

export function readSvtSession(electionUuid) {
  try {
    const raw = sessionStorage.getItem(storageKey(electionUuid))
    if (!raw) return null
    if (raw.trim().startsWith('{')) {
      const data = JSON.parse(raw)
      const code = normalizeSvt(data?.code || '')
      return {
        code: isValidSvtFormat(code) ? code : '',
        expires_at: data.expires_at || null,
        status: data.status || 'validated',
      }
    }
    const code = normalizeSvt(raw)
    if (!isValidSvtFormat(code)) return null
    return { code, expires_at: null, status: 'validated' }
  } catch {
    return null
  }
}

export function writeSvtSession(electionUuid, { code, expires_at = null, status = 'validated' } = {}) {
  const normalized = normalizeSvt(code)
  if (!isValidSvtFormat(normalized)) return
  sessionStorage.setItem(
    storageKey(electionUuid),
    JSON.stringify({
      code: normalized,
      expires_at,
      status,
      saved_at: new Date().toISOString(),
    }),
  )
}

export function clearSvtSession(electionUuid) {
  sessionStorage.removeItem(storageKey(electionUuid))
}

export function isSvtSessionExpired(session, serverExpiresAt = null) {
  const stamp = serverExpiresAt || session?.expires_at
  if (!stamp) return false
  const ms = Date.parse(stamp)
  if (Number.isNaN(ms)) return false
  return ms <= Date.now()
}
