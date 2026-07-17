/**
 * Short UI beeps via Web Audio (no asset files).
 * Browsers may require a prior user gesture before audio unlocks.
 */

let audioCtx = null

function getCtx() {
  if (typeof window === 'undefined') return null
  const AC = window.AudioContext || window.webkitAudioContext
  if (!AC) return null
  if (!audioCtx) audioCtx = new AC()
  return audioCtx
}

/** Call from a click/tap so later automatic beeps are allowed. */
export function unlockAudio() {
  const ctx = getCtx()
  if (!ctx) return
  if (ctx.state === 'suspended') {
    ctx.resume().catch(() => {})
  }
}

/**
 * @param {'tick'|'warn'|'urgent'|'alert'|'expire'|'chime'} kind
 */
export function playBeep(kind = 'tick') {
  const ctx = getCtx()
  if (!ctx) return
  if (ctx.state === 'suspended') {
    ctx.resume().catch(() => {})
  }

  const presets = {
    tick: { freq: 880, ms: 70, gain: 0.045, type: 'sine' },
    warn: { freq: 740, ms: 110, gain: 0.06, type: 'triangle' },
    urgent: { freq: 990, ms: 140, gain: 0.08, type: 'square' },
    alert: { freq: 660, ms: 160, gain: 0.09, type: 'square' },
    expire: { freq: 420, ms: 280, gain: 0.1, type: 'sawtooth' },
    chime: { freq: 784, ms: 180, gain: 0.055, type: 'sine' },
  }
  const p = presets[kind] || presets.tick
  const now = ctx.currentTime
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()
  osc.type = p.type
  osc.frequency.setValueAtTime(p.freq, now)
  gain.gain.setValueAtTime(0.0001, now)
  gain.gain.exponentialRampToValueAtTime(p.gain, now + 0.012)
  gain.gain.exponentialRampToValueAtTime(0.0001, now + p.ms / 1000)
  osc.connect(gain)
  gain.connect(ctx.destination)
  osc.start(now)
  osc.stop(now + p.ms / 1000 + 0.02)
}

/**
 * Soft two-tone notification chime (clean sine, no harsh square buzz).
 */
export function playNotificationChime() {
  const ctx = getCtx()
  if (!ctx) return
  if (ctx.state === 'suspended') {
    ctx.resume().catch(() => {})
  }

  const now = ctx.currentTime
  const tones = [
    { freq: 523.25, at: 0, ms: 160, gain: 0.05 }, // C5
    { freq: 659.25, at: 0.12, ms: 220, gain: 0.045 }, // E5
  ]

  for (const tone of tones) {
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    const start = now + tone.at
    osc.type = 'sine'
    osc.frequency.setValueAtTime(tone.freq, start)
    gain.gain.setValueAtTime(0.0001, start)
    gain.gain.exponentialRampToValueAtTime(tone.gain, start + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.0001, start + tone.ms / 1000)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start(start)
    osc.stop(start + tone.ms / 1000 + 0.04)
  }
}
