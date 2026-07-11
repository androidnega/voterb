<template>
  <div class="countdown" :class="`countdown--${timing.phase}`">
    <div v-if="!timing.expired" class="countdown-row" role="timer" :aria-label="ariaLabel">
      <span class="countdown-prefix">{{ timing.label }}</span>
      <span class="countdown-clock">
        <span class="countdown-segment">{{ pad(timing.days) }}<small>d</small></span>
        <span class="countdown-dot" aria-hidden="true">·</span>
        <span class="countdown-segment">{{ pad(timing.hours) }}<small>h</small></span>
        <span class="countdown-dot" aria-hidden="true">·</span>
        <span class="countdown-segment">{{ pad(timing.minutes) }}<small>m</small></span>
        <span class="countdown-dot" aria-hidden="true">·</span>
        <span class="countdown-segment countdown-segment--sec">{{ pad(timing.seconds) }}<small>s</small></span>
      </span>
    </div>

    <p v-else class="countdown-ended">{{ timing.label }}</p>

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
  display: grid;
  gap: 0.3rem;
}

.countdown-row {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.45rem 0.55rem;
}

.countdown-prefix {
  font-size: 0.68rem;
  font-weight: 500;
  color: #a8a29e;
  letter-spacing: 0.01em;
}

.countdown--open .countdown-prefix {
  color: var(--vb-accent, #0f766e);
}

.countdown-clock {
  display: inline-flex;
  align-items: baseline;
  gap: 0.2rem;
  font-variant-numeric: tabular-nums;
}

.countdown-segment {
  font-size: 0.92rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: #1c1917;
  line-height: 1;
}

.countdown--open .countdown-segment {
  color: var(--vb-accent, #0f766e);
}

.countdown-segment small {
  margin-left: 0.05rem;
  font-size: 0.62rem;
  font-weight: 600;
  color: #a8a29e;
}

.countdown-segment--sec {
  min-width: 2.1rem;
}

.countdown-dot {
  color: #d6d3d1;
  font-weight: 700;
  font-size: 0.75rem;
  line-height: 1;
}

.countdown-ended {
  margin: 0;
  font-size: 0.75rem;
  font-weight: 500;
  color: #78716c;
}

.countdown-absolute {
  margin: 0;
  font-size: 0.65rem;
  color: #a8a29e;
}

@media (min-width: 768px) {
  .countdown-prefix {
    font-size: 0.72rem;
  }

  .countdown-segment {
    font-size: 1.05rem;
  }

  .countdown-segment small {
    font-size: 0.68rem;
  }
}
</style>
