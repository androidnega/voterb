<template>
  <div class="countdown" :class="[`countdown--${timing.phase}`, variantClass, urgencyClass]">
    <p class="countdown-label">{{ displayLabel }}</p>

    <div v-if="!timing.expired" class="countdown-track" role="timer" :aria-label="ariaLabel">
      <div class="countdown-unit">
        <span class="countdown-value">{{ pad(timing.days) }}</span>
        <span class="countdown-name">days</span>
      </div>
      <div class="countdown-unit">
        <span class="countdown-value">{{ pad(timing.hours) }}</span>
        <span class="countdown-name">hrs</span>
      </div>
      <div class="countdown-unit">
        <span class="countdown-value">{{ pad(timing.minutes) }}</span>
        <span class="countdown-name">min</span>
      </div>
      <div class="countdown-unit countdown-unit--sec">
        <span class="countdown-value">{{ pad(timing.seconds) }}</span>
        <span class="countdown-name">sec</span>
      </div>
    </div>

    <p v-else class="countdown-ended">{{ endedCopy }}</p>

    <p v-if="timing.target && !timing.expired" class="countdown-absolute">
      {{ timing.absoluteLabel }} {{ formatElectionMoment(timing.target) }}
    </p>
  </div>
</template>

<script setup>
import { computed, toRef, watch, ref } from 'vue'
import {
  formatCountdownUnit,
  formatElectionMoment,
  getElectionTiming,
  useNowTicker,
} from '@/composables/useCountdown'
import { playBeep, unlockAudio } from '@/utils/beep'

const props = defineProps({
  election: { type: Object, required: true },
  /** Override the default phase label (e.g. "Voting closes in") */
  label: { type: String, default: '' },
  /** Visual variant: default | done */
  variant: { type: String, default: 'default' },
  /** Audible ticks when time is running short */
  beep: { type: Boolean, default: true },
})

const now = useNowTicker()
const election = toRef(props, 'election')
const lastBeepKey = ref('')

const timing = computed(() => getElectionTiming(election.value, now.value))
const pad = (value) => formatCountdownUnit(value)

const displayLabel = computed(() => {
  if (props.label) return props.label
  if (timing.value.phase === 'open') return 'Voting closes in'
  if (timing.value.phase === 'upcoming') return 'Voting opens in'
  return timing.value.label
})

const endedCopy = computed(() => {
  if (timing.value.phase === 'closed') return 'Voting has closed'
  return timing.value.label
})

const variantClass = computed(() => (
  props.variant === 'done' ? 'countdown--done' : ''
))

const totalSeconds = computed(() => Math.max(0, Math.floor((timing.value.totalMs || 0) / 1000)))

const urgencyClass = computed(() => {
  if (timing.value.expired) return ''
  const s = totalSeconds.value
  if (s <= 30) return 'countdown--critical'
  if (s <= 120) return 'countdown--urgent'
  if (s <= 300) return 'countdown--warn'
  return ''
})

const ariaLabel = computed(() => {
  if (timing.value.expired) return endedCopy.value
  return `${displayLabel.value} ${timing.value.days} days, ${timing.value.hours} hours, ${timing.value.minutes} minutes, ${timing.value.seconds} seconds`
})

watch(
  () => [props.beep, timing.value.phase, totalSeconds.value, timing.value.expired],
  ([beepOn, phase, seconds, expired]) => {
    if (!beepOn || expired || !['open', 'upcoming'].includes(phase)) return
    if (seconds > 300) return
    let key = null
    let kind = 'tick'
    if (seconds <= 10) {
      key = `c-${seconds}`
      kind = 'urgent'
    } else if (seconds <= 60) {
      key = `u-${Math.floor(seconds / 5)}`
      kind = 'warn'
    } else {
      key = `m-${Math.floor(seconds / 30)}`
      kind = 'tick'
    }
    if (key && key !== lastBeepKey.value) {
      lastBeepKey.value = key
      unlockAudio()
      playBeep(kind)
    }
  },
)
</script>

<style scoped>
.countdown {
  margin-top: 0.15rem;
  padding: 0.7rem 0.75rem;
  border-radius: 0.7rem;
  background: #f8f7f4;
  border: 1px solid #f0eeea;
  display: grid;
  gap: 0.45rem;
}

.countdown--open {
  background: linear-gradient(180deg, #f7fdfb 0%, #f0fdf9 100%);
  border-color: #d7f3ec;
}

.countdown--done {
  background: #fafaf9;
  border-color: #ebe8e2;
}

.countdown--done.countdown--open {
  background: linear-gradient(180deg, #fbfefd 0%, #f4faf8 100%);
  border-color: #dceee9;
}

.countdown--warn {
  border-color: #f5d0a9;
  background: linear-gradient(180deg, #fffaf3 0%, #fff4e6 100%);
}

.countdown--urgent,
.countdown--critical {
  border-color: #fecaca;
  background: linear-gradient(180deg, #fff5f5 0%, #fee2e2 100%);
}

.countdown--critical .countdown-value {
  animation: countdown-flash 1s ease-in-out infinite;
}

.countdown-label {
  margin: 0;
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: #a8a29e;
}

.countdown--open .countdown-label {
  color: var(--vb-accent, #0f766e);
}

.countdown--done .countdown-label {
  color: #78716c;
}

.countdown--warn .countdown-label,
.countdown--warn .countdown-value {
  color: #c2410c;
}

.countdown--urgent .countdown-label,
.countdown--urgent .countdown-value,
.countdown--critical .countdown-label,
.countdown--critical .countdown-value {
  color: #b91c1c;
}

.countdown-track {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.35rem;
}

.countdown-unit {
  display: grid;
  justify-items: center;
  gap: 0.2rem;
  padding: 0.45rem 0.2rem;
  border-radius: 0.55rem;
  background: #fff;
  border: 1px solid #ece9e2;
}

.countdown--open .countdown-unit {
  border-color: #ccefe8;
}

.countdown--done .countdown-unit {
  border-color: #ebe8e2;
  background: #fff;
}

.countdown-value {
  font-size: 1rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.02em;
  color: #1c1917;
  line-height: 1;
}

.countdown--open .countdown-value {
  color: var(--vb-accent, #0f766e);
}

.countdown--done .countdown-value {
  color: #44403c;
}

.countdown-name {
  font-size: 0.52rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #a8a29e;
}

.countdown-ended {
  margin: 0;
  font-size: 0.75rem;
  font-weight: 500;
  color: #78716c;
}

.countdown-absolute {
  margin: 0;
  font-size: 0.62rem;
  color: #a8a29e;
  text-align: center;
}

@keyframes countdown-flash {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.55; }
}

@media (max-width: 639px) {
  .countdown {
    padding: 0.65rem 0.6rem;
    gap: 0.4rem;
  }

  .countdown-track {
    gap: 0.28rem;
  }

  .countdown-unit {
    padding: 0.5rem 0.15rem;
    border-radius: 0.5rem;
  }

  .countdown-value {
    font-size: 0.95rem;
  }

  .countdown-name {
    font-size: 0.48rem;
  }
}

@media (min-width: 768px) {
  .countdown {
    padding: 0.75rem 0.85rem;
  }

  .countdown-value {
    font-size: 1.1rem;
  }
}
</style>
