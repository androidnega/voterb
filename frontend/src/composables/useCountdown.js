import { ref, onMounted, onUnmounted, computed } from 'vue'

export function parseCountdown(targetDate, now = Date.now()) {
  if (!targetDate) {
    return { expired: true, days: 0, hours: 0, minutes: 0, seconds: 0, totalMs: 0 }
  }

  const diff = new Date(targetDate).getTime() - now
  if (diff <= 0) {
    return { expired: true, days: 0, hours: 0, minutes: 0, seconds: 0, totalMs: 0 }
  }

  const totalSeconds = Math.floor(diff / 1000)
  return {
    expired: false,
    days: Math.floor(totalSeconds / 86400),
    hours: Math.floor((totalSeconds % 86400) / 3600),
    minutes: Math.floor((totalSeconds % 3600) / 60),
    seconds: totalSeconds % 60,
    totalMs: diff,
  }
}

export function getElectionTiming(election, now = Date.now()) {
  const startMs = election?.start_date ? new Date(election.start_date).getTime() : 0
  const endMs = election?.end_date ? new Date(election.end_date).getTime() : 0
  const status = election?.status

  if (!startMs || !endMs) {
    return {
      phase: 'unknown',
      label: 'Schedule',
      target: null,
      ...parseCountdown(null, now),
    }
  }

  // Once voting is explicitly started, always count toward the closing time,
  // even if an administrator opened it before its originally scheduled start.
  if (['open', 'paused'].includes(status) && now < endMs) {
    return {
      phase: 'open',
      label: 'Closes in',
      target: election.end_date,
      absoluteLabel: 'Closes',
      ...parseCountdown(election.end_date, now),
    }
  }

  if (['closed', 'archived'].includes(status)) {
    return {
      phase: 'closed',
      label: 'Voting ended',
      target: election.end_date,
      absoluteLabel: 'Closed',
      expired: true,
      days: 0,
      hours: 0,
      minutes: 0,
      seconds: 0,
      totalMs: 0,
    }
  }

  if (now < startMs) {
    return {
      phase: 'upcoming',
      label: 'Opens in',
      target: election.start_date,
      absoluteLabel: 'Opens',
      ...parseCountdown(election.start_date, now),
    }
  }

  if (now < endMs) {
    return {
      phase: 'open',
      label: 'Closes in',
      target: election.end_date,
      absoluteLabel: 'Closes',
      ...parseCountdown(election.end_date, now),
    }
  }

  return {
    phase: 'closed',
    label: 'Voting ended',
    target: election.end_date,
    absoluteLabel: 'Closed',
    expired: true,
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
    totalMs: 0,
  }
}

export function formatCountdownUnit(value) {
  return String(value).padStart(2, '0')
}

export function formatElectionMoment(date) {
  if (!date) return 'TBA'
  return new Date(date).toLocaleString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const sharedNow = ref(Date.now())
let tickerCount = 0
let tickerId = null

export function useNowTicker(intervalMs = 1000) {
  onMounted(() => {
    tickerCount += 1
    if (!tickerId) {
      tickerId = window.setInterval(() => {
        sharedNow.value = Date.now()
      }, intervalMs)
    }
  })

  onUnmounted(() => {
    tickerCount -= 1
    if (tickerCount <= 0 && tickerId) {
      window.clearInterval(tickerId)
      tickerId = null
    }
  })

  return sharedNow
}

export function useElectionTiming(electionRef) {
  const now = useNowTicker()
  return computed(() => getElectionTiming(electionRef.value, now.value))
}
