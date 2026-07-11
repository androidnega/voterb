<template>
  <div class="countdown" :class="`countdown--${timing.phase}`">
    <p class="countdown-label">{{ timing.label }}</p>

    <div v-if="!timing.expired" class="countdown-grid" role="timer" :aria-label="ariaLabel">
      <div class="countdown-unit">
        <span class="countdown-value">{{ pad(timing.days) }}</span>
        <span class="countdown-name">days</span>
      </div>
      <span class="countdown-sep" aria-hidden="true">:</span>
      <div class="countdown-unit">
        <span class="countdown-value">{{ pad(timing.hours) }}</span>
        <span class="countdown-name">hrs</span>
      </div>
      <span class="countdown-sep" aria-hidden="true">:</span>
      <div class="countdown-unit">
        <span class="countdown-value">{{ pad(timing.minutes) }}</span>
        <span class="countdown-name">min</span>
      </div>
      <span class="countdown-sep" aria-hidden="true">:</span>
      <div class="countdown-unit">
        <span class="countdown-value">{{ pad(timing.seconds) }}</span>
        <span class="countdown-name">sec</span>
      </div>
    </div>

    <p v-else class="countdown-ended">This ballot is no longer accepting votes.</p>

    <p v-if="timing.target" class="countdown-absolute">
      {{ timing.absoluteLabel }} {{ formatElectionMoment(timing.target) }}
    </p>
  </div>
</template>

<script setup>
import { computed, toRef } from 'vue'
import {
  formatCountdownUnit,
  formatElectionMoment,
  getElectionTiming,
  useNowTicker,
} from '@/composables/useCountdown'

const props = defineProps({
  election: { type: Object, required: true },
})

const now = useNowTicker()
const election = toRef(props, 'election')

const timing = computed(() => getElectionTiming(election.value, now.value))

const pad = (value) => formatCountdownUnit(value)

const ariaLabel = computed(() => {
  if (timing.value.expired) return timing.value.label
  return `${timing.value.label} ${timing.value.days} days, ${timing.value.hours} hours, ${timing.value.minutes} minutes, ${timing.value.seconds} seconds`
})
</script>

<style scoped>
.countdown {
  margin-top: 0.9rem;
  padding: 0.85rem 0.9rem;
  border-radius: 0.7rem;
  background: linear-gradient(180deg, #f8f7f4 0%, #f3f2ee 100%);
  border: 1px solid #e8e5df;
}

.countdown--open {
  background: linear-gradient(180deg, #f0fdf9 0%, #ecfdf5 100%);
  border-color: var(--vb-accent-border, #99f6e4);
}

.countdown--closed {
  background: #fafaf9;
  border-color: #e7e5e4;
}

.countdown-label {
  margin: 0;
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #78716c;
}

.countdown--open .countdown-label {
  color: var(--vb-accent, #0f766e);
}

.countdown-grid {
  margin-top: 0.55rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
}

.countdown-unit {
  min-width: 2.65rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
}

.countdown-value {
  width: 100%;
  padding: 0.4rem 0.2rem;
  border-radius: 0.45rem;
  background: #fff;
  border: 1px solid #e7e5e4;
  font-size: 0.95rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.04em;
  color: #1c1917;
  text-align: center;
  line-height: 1;
}

.countdown--open .countdown-value {
  border-color: #ccefe8;
  color: var(--vb-accent, #0f766e);
}

.countdown-name {
  font-size: 0.52rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #a8a29e;
}

.countdown-sep {
  margin-top: -0.55rem;
  font-size: 0.85rem;
  font-weight: 700;
  color: #d6d3d1;
}

.countdown-ended {
  margin: 0.55rem 0 0;
  font-size: 0.75rem;
  font-weight: 600;
  color: #78716c;
}

.countdown-absolute {
  margin: 0.55rem 0 0;
  font-size: 0.65rem;
  color: #a8a29e;
  text-align: center;
}

@media (max-width: 380px) {
  .countdown-unit {
    min-width: 2.35rem;
  }

  .countdown-value {
    font-size: 0.82rem;
    padding: 0.35rem 0.15rem;
  }

  .countdown-grid {
    gap: 0.2rem;
  }
}
</style>
