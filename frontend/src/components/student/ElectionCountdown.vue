<template>
  <div class="countdown" :class="`countdown--${timing.phase}`">
    <p class="countdown-label">{{ timing.label }}</p>

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
