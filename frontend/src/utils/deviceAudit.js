/**
 * Collect authentic device / OS signals for vote-cast audits.
 * Uses User-Agent Client Hints when available; never includes ballot data.
 */

async function sha256Hex(text) {
  if (typeof crypto !== 'undefined' && crypto.subtle) {
    const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))
    return Array.from(new Uint8Array(buf))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('')
  }
  // Fallback non-crypto hash for ancient browsers
  let h = 0
  for (let i = 0; i < text.length; i += 1) {
    h = (Math.imul(31, h) + text.charCodeAt(i)) | 0
  }
  return `fallback-${(h >>> 0).toString(16)}`
}

function guessDeviceType() {
  const ua = navigator.userAgent || ''
  if (/iPad|Tablet/i.test(ua)) return 'tablet'
  if (/Mobi|iPhone|Android/i.test(ua)) return 'mobile'
  return 'desktop'
}

function parseUaBrowser(ua) {
  const patterns = [
    [/Edg\/([\d.]+)/, 'Edge'],
    [/OPR\/([\d.]+)/, 'Opera'],
    [/Chrome\/([\d.]+)/, 'Chrome'],
    [/Firefox\/([\d.]+)/, 'Firefox'],
    [/Version\/([\d.]+).*Safari/, 'Safari'],
  ]
  for (const [re, name] of patterns) {
    const m = ua.match(re)
    if (m) return { browser_name: name, browser_version: m[1] }
  }
  return { browser_name: 'Unknown', browser_version: '' }
}

async function readClientHints() {
  const uaData = navigator.userAgentData
  if (!uaData || typeof uaData.getHighEntropyValues !== 'function') {
    return null
  }
  try {
    const hints = await uaData.getHighEntropyValues([
      'architecture',
      'bitness',
      'model',
      'platformVersion',
      'uaFullVersion',
      'fullVersionList',
    ])
    const brand =
      (hints.fullVersionList || uaData.brands || []).find(
        (b) => b.brand && !/Not.?A.?Brand/i.test(b.brand),
      ) || (uaData.brands || [])[0]

    return {
      hints_source: 'client_hints',
      platform: uaData.platform || hints.platform || '',
      platform_version: hints.platformVersion || '',
      architecture: hints.architecture || '',
      bitness: hints.bitness || '',
      model: hints.model || '',
      browser_name: brand?.brand || '',
      browser_version: brand?.version || hints.uaFullVersion || '',
      operating_system: [uaData.platform || hints.platform, hints.platformVersion]
        .filter(Boolean)
        .join(' ')
        .trim(),
      device_type: uaData.mobile ? 'mobile' : guessDeviceType(),
    }
  } catch {
    return null
  }
}

function readGeoOnce(timeoutMs = 4000) {
  if (!navigator.geolocation) return Promise.resolve(null)
  return new Promise((resolve) => {
    const timer = setTimeout(() => resolve(null), timeoutMs)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        clearTimeout(timer)
        resolve({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
        })
      },
      () => {
        clearTimeout(timer)
        resolve(null)
      },
      { enableHighAccuracy: false, maximumAge: 120000, timeout: timeoutMs },
    )
  })
}

/**
 * @param {{ includeLocation?: boolean }} [options]
 */
export async function collectVoteAuditContext(options = {}) {
  const includeLocation = options.includeLocation !== false
  const ua = navigator.userAgent || ''
  const hints = await readClientHints()
  const uaBrowser = parseUaBrowser(ua)

  const base = {
    user_agent: ua,
    device_type: hints?.device_type || guessDeviceType(),
    operating_system: hints?.operating_system || navigator.platform || 'Unknown',
    platform: hints?.platform || navigator.platform || '',
    platform_version: hints?.platform_version || '',
    architecture: hints?.architecture || '',
    bitness: hints?.bitness || '',
    model: hints?.model || '',
    browser_name: hints?.browser_name || uaBrowser.browser_name,
    browser_version: hints?.browser_version || uaBrowser.browser_version,
    hints_source: hints?.hints_source || 'user_agent',
    languages: Array.from(navigator.languages || [navigator.language].filter(Boolean)),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || '',
    screen: {
      width: window.screen?.width,
      height: window.screen?.height,
      dpr: window.devicePixelRatio || 1,
    },
    hardware_concurrency: navigator.hardwareConcurrency || null,
    device_memory_gb: navigator.deviceMemory || null,
    touch_points: navigator.maxTouchPoints || 0,
  }

  const fingerprintSeed = [
    base.operating_system,
    base.platform,
    base.platform_version,
    base.architecture,
    base.browser_name,
    base.languages.join(','),
    base.timezone,
    `${base.screen.width}x${base.screen.height}@${base.screen.dpr}`,
    String(base.hardware_concurrency || ''),
    String(base.device_memory_gb || ''),
    String(base.touch_points || ''),
  ].join('|')

  base.fingerprint = await sha256Hex(fingerprintSeed)

  if (includeLocation) {
    base.location = await readGeoOnce()
  }

  return base
}

export function cacheVoteAuditContext(electionUuid, context) {
  try {
    sessionStorage.setItem(`vote_audit_ctx:${electionUuid}`, JSON.stringify(context))
  } catch {
    /* ignore quota */
  }
}

export function readCachedVoteAuditContext(electionUuid) {
  try {
    const raw = sessionStorage.getItem(`vote_audit_ctx:${electionUuid}`)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}
